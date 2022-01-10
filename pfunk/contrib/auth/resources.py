from pfunk.client import q
from pfunk.resources import Function, Role, Index


class AuthFunction(Function):

    def get_role(self):
        return "admin"


class LoginUser(AuthFunction):
    def get_body(self):
        return q.query(
            q.lambda_(["input"],
                      q.let({
                          "user": q.match(q.index("unique_User_username"), q.select("username", q.var("input")))
                      },
                          q.if_(
                              q.equals(
                                  q.select(
                                      ["data", "account_status"],
                                      q.get(q.var("user"))
                                  ),
                                  "ACTIVE"
                              ),

                              q.select(
                                  "secret",
                                  q.login(
                                      q.var("user"),
                                      {
                                          "password": q.select("password", q.var("input")),
                                          "ttl": q.time_add(q.now(), 7, 'days')
                                      }
                                  )
                              ),
                              q.abort("Account is not active. Please check email for activation.")
                          )
                      )
                      )
        )


class LogoutUser(AuthFunction):

    def get_body(self):
        return q.query(
            q.lambda_([],
                      q.logout(True)
                      )
        )


class UpdatePassword(AuthFunction):
    def get_body(self):
        return q.query(q.lambda_(["input"],
                                 q.if_(
                                     q.identify(q.current_identity(),
                                                q.select("current_password", q.var("input"))),
                                     q.update(q.current_identity(), {
                                         "credentials": {"password": q.select("new_password", q.var("input"))}
                                     }),
                                     q.abort("Wrong current password.")
                                 )
                                 )
                       )


class CreateUser(AuthFunction):
    def get_body(self):
        data_dict = {
            "data": self.collection.get_fields(),
            "credentials": {
                self.collection._credential_field: q.select(self.collection._credential_field, q.var("input"))
            }
        }
        return q.query(
            q.lambda_(["input"],
                      q.let(
                          {
                              'result': q.create(
                                  q.collection(self.collection.get_collection_name()),
                                  data_dict),
                              'input': q.var('input')
                          },
                          # If 'groups' key is an array
                          q.if_(
                              q.is_array(q.select('groups', q.var('input'))),
                              q.foreach(
                                  q.lambda_(
                                      'group',
                                      q.create(
                                          q.collection(self.collection._base_properties.get('groups').relation_name),
                                          {'data': {
                                              'userID': q.select('ref', q.var('result')),
                                              'groupID': q.var('group')
                                          }}
                                      )
                                  )
                                  ,
                                  q.select('groups', q.var('input'))
                              ),
                              q.abort('Groups not defined.')
                          )
                      )
                      ))


class Public(Role):

    def get_membership_lambda(self):
        return

    def get_function_lambda(self):
        return q.query(
            q.lambda_(['data'],
                      q.equals(
                          q.select('account_status', q.select('data',
                                                              q.match(q.index('unique_User_username',
                                                                              q.select('username', q.var('data')))))),
                          "ACTIVE"
                      )
                      ))

    def get_privileges(self):
        return [
            {
                "resource": q.function("login_user"),
                "actions": {
                    "call": self.get_function_lambda()
                }
            },
            {
                "resource": q.function("update_password"),
                "actions": {
                    "call": True
                }
            },
            {
                "resource": q.function("logout_user"),
                "actions": {
                    "call": True
                }
            }

        ]


class UserRole(Role):

    def get_privileges(self):
        return [
            {
                "resource": q.collection(self.collection.get_collection_name()),
                "actions": {
                    'read': self.get_lambda('read')
                }
            }
        ]

    def get_lambda(self, resource_type):
        lambda_args = ["object_ref"]
        return q.query(
            q.lambda_(lambda_args,
                      q.equals(
                          q.var('object_ref'),
                          q.current_identity()
                      )
                      )
        )


class GenericAuthorizationRole(Role):
    user_table = 'User'
    current_user_field = 'user'
    name_suffix = 'user_based_crud_role'

    def get_name(self):
        return self.name or f"{self.collection.get_class_name()}_{self.name_suffix}"

    def get_privileges(self):
        priv_list = [
            {
                "resource": q.collection(self.collection.get_collection_name()),
                "actions": {
                    'read': self.get_lambda('read'),
                    'write': self.get_lambda('write'),
                    'create': self.get_lambda('create'),
                    'delete': self.get_lambda('delete'),
                }
            },
            {
                "resource": q.index(self.relation_index_name),
                "actions": {
                    "read": True
                }
            },
            {
                "resource": q.index(self.collection.all_index_name()),
                "actions": {
                    "read": True
                }
            },
        ]
        priv_list.extend([
            {
                "resource": q.index(i().get_name()),
                "actions": {
                    "read": True
                }
            }
            for i in self.collection.collection_indexes
        ])
        priv_list.extend([
            {
                "resource": q.function(i(self.collection).get_name()),
                "actions": {
                    "call": True
                }
            }
            for i in self.collection.collection_functions
        ])
        return priv_list


class GenericUserBasedRole(GenericAuthorizationRole):
    relation_index_name = 'users_groups_by_user'

    def get_lambda(self, resource_type):
        if resource_type == 'write':
            lambda_args = ["old_object", "new_object", "object_ref"]
            user_ref = q.select(self.current_user_field,
                                q.select('data', q.var('old_object')))
            return q.query(
                q.lambda_(lambda_args,
                          q.and_(
                              q.equals(
                                  user_ref,
                                  q.current_identity()
                              ),
                              q.equals(
                                  q.select(self.current_user_field, q.select('data', q.var('new_object'))),
                                  q.current_identity()
                              )
                          )

                          )
            )
        elif resource_type == 'create':
            lambda_args = ["new_object"]
            user_ref = q.select(self.current_user_field,
                                q.select('data', q.var('new_object')))
        elif resource_type == 'read' or resource_type == 'delete':
            lambda_args = ["object_ref"]
            user_ref = q.select(self.current_user_field,
                                q.select('data', q.get(q.var('object_ref'))))

        return q.query(
            q.lambda_(lambda_args,
                      q.equals(
                          user_ref,
                          q.current_identity()
                      )
                      )
        )


class GenericGroupBasedRole(GenericAuthorizationRole):
    relation_index_name = 'users_groups_by_group_and_user'
    through_user_field = 'userID'
    current_group_field = 'group'
    permissions_field = 'permissions'
    user_table = 'User'
    name_suffix = 'group_based_crud_role'

    def get_lambda(self, resource_type):
        perm = f'{self.collection.get_collection_name()}-{resource_type}'.lower()
        if resource_type == 'write':
            group_ref = q.select(self.current_group_field,
                                 q.select('data', q.var('old_object')))
            lambda_args = ["old_object", "new_object", "object_ref"]

            return q.query(
                q.lambda_(lambda_args,
                          q.and_(
                              q.equals(
                                  # User ID from index
                                  q.select(0, q.filter_(lambda i: q.equals(perm, i),
                                                        q.select(self.permissions_field,
                                                                 q.get(
                                                                     q.match(
                                                                         q.index(self.relation_index_name),
                                                                         group_ref,
                                                                         q.current_identity()
                                                                     )
                                                                 )))),
                                  perm
                              ),
                              q.equals(
                                  q.select(self.current_group_field, q.select('data', q.var('old_object'))),
                                  q.select(self.current_group_field, q.select('data', q.var('new_object'))),
                              )
                          )
                          )
            )
        elif resource_type == 'create':
            group_ref = q.select(self.current_group_field,
                                 q.select('data', q.var('new_object')))
            lambda_args = ["new_object"]
        elif resource_type == 'read' or resource_type == 'delete':
            group_ref = q.select(self.current_group_field,
                                 q.select('data', q.get(q.var('object_ref'))))
            lambda_args = ["object_ref"]

        return q.query(
            q.lambda_(
                lambda_args,
                q.equals(
                    q.select(0, q.filter_(lambda i: q.equals(perm, i),
                                          q.select(self.permissions_field,
                                                   q.select("data",
                                                            q.get(q.match(
                                                                q.index(self.relation_index_name),
                                                                group_ref,
                                                                q.current_identity()
                                                            )))))),
                    perm
                )
            )
        )
