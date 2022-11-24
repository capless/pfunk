from tokenize import group
from envs import env

from pfunk.client import q
from pfunk.resources import Function, Role

# Global collections
USER_CLASS = env('USER_COLLECTION', 'User')
GROUP_CLASS = env('GROUP_COLLECTION', 'Group')


class AuthFunction(Function):

    def get_role(self):
        return "admin"


class LoginUser(AuthFunction):
    def get_body(self):
        return q.query(
            q.lambda_(["input"],
                      q.let({
                          "user": q.match(q.index(f"unique_{self.collection.__class__.__name__}_username"), q.select("username", q.var("input")))
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
                              q.abort(
                                  "Account is not active. Please check email for activation.")
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
                self.collection._credential_field: q.select(
                    self.collection._credential_field, q.var("input"))
            }
        }
        return q.query(
            q.lambda_(["input"],
                      q.let(
                          {
                              'result': q.create(
                                  q.collection(
                                      self.collection.get_collection_name()),
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
                                          q.collection(self.collection._base_properties.get(
                                              'groups').relation_name),
                                          {'data': {
                                              'userID': q.select('ref', q.var('result')),
                                              'groupID': q.var('group')
                                          }}
                                      )
                                  ),
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
                                                              q.match(q.index(f'unique_{self.collection.__class__.__name__}_username',
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

    def get_relation_index_name(self):
        """ Returns the index name of the created permission index of group and user -> 'usergroups_by_userID_and_groupID' """
        return 'usergroups_by_userID_and_groupID'

    def get_user_table(self):
        return USER_CLASS

    def get_group_table(self):
        return GROUP_CLASS

    def get_name_suffix(self):
        return f'{self.collection.get_user_field().lower()}_based_crud_role'

    def get_name(self):
        return self.name or f"{self.collection.get_class_name()}_{self.get_name_suffix()}"

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
                "resource": q.index(self.get_relation_index_name()),
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
    """ Generic set of permissions for entity to user relationship """

    def get_relation_index_name(self):
        """ Returns the user-group by user index name 

            Formatted as: {user_group_relation_name}_by_{user_class}
        """
        # Acquires the `groups` field from the user collection
        user_field = self.collection.get_user_field()
        if user_field:
            user_field = user_field.lower()
        else:
            return None
        user_col = self.collection._base_properties.get(user_field)
        user_col = user_col.get_foreign_class()
        user_groups = user_col._base_properties.get("groups")

        if user_groups:
            relation_index_name = (user_groups.relation_name
                                   + '_by_'
                                   + self.get_user_table().lower())
            return relation_index_name
        return None

    def get_lambda(self, resource_type):
        current_user_field = self.collection.get_user_field()
        if resource_type == 'write':
            lambda_args = ["old_object", "new_object", "object_ref"]
            user_ref = q.select(current_user_field,
                                q.select('data', q.var('old_object')))
            return q.query(
                q.lambda_(lambda_args,
                          q.and_(
                              q.equals(
                                  user_ref,
                                  q.current_identity()
                              ),
                              q.equals(
                                  q.select(current_user_field, q.select(
                                      'data', q.var('new_object'))),
                                  q.current_identity()
                              )
                          )

                          )
            )
        elif resource_type == 'create':
            lambda_args = ["new_object"]
            user_ref = q.select(current_user_field,
                                q.select('data', q.var('new_object')))
        elif resource_type == 'read' or resource_type == 'delete':
            lambda_args = ["object_ref"]
            user_ref = q.select(current_user_field,
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
    permissions_field = 'permissions'
    user_table = USER_CLASS
    group_table = GROUP_CLASS
    through_user_field = USER_CLASS.lower() + 'ID'

    def get_name_suffix(self):
        return f'{self.group_table.lower()}_based_crud_role'
    
    def get_lambda(self, resource_type):
        """ Returns the lambda function for giving the permission to Group-based entities 
        
            Allows modification if:
                1. You belong to the group that owns the document
                2. You have the create permission to perform the action (create, read, write, and delete)
        """
        current_group_field = self.collection.get_group_field().lower()
        perm = f'{resource_type}'.lower()

        if resource_type == 'write':
            group_ref = q.select(current_group_field,
                                 q.select('data', q.var('old_object')))
            lambda_args = ["old_object", "new_object", "object_ref"]

            return q.query(
                q.lambda_(lambda_args,
                          q.and_(
                              q.equals(
                                  # User ID from index
                                  q.select(0, q.filter_(lambda i: q.equals(perm, i),
                                                        q.select(self.permissions_field,
                                                        q.select("data",
                                                                 q.get(
                                                                     q.match(
                                                                         q.index(
                                                                             self.get_relation_index_name()),
                                                                         q.current_identity(),
                                                                         group_ref
                                                                     )
                                                                 ))))),
                                  perm
                              ),
                              q.equals(
                                  q.select(current_group_field, q.select(
                                      'data', q.var('old_object'))),
                                  q.select(current_group_field, q.select(
                                      'data', q.var('new_object'))),
                              )
                          )
                          )
            )
        elif resource_type == 'create':
            lambda_args = ["new_object"]
            group_ref = q.select(current_group_field,
                                 q.select('data', q.var('new_object')))
        elif resource_type == 'read' or resource_type == 'delete':
            lambda_args = ["object_ref"]
            group_ref = q.select(current_group_field,
                                 q.select('data', q.get(q.var('object_ref'))))

        return q.query(
            q.lambda_(
                lambda_args,
                q.equals(
                    # NOTE: After acquiring the instance of `UserGroup`, filter the result: permission field
                    # that matches the `perm` variable AND then see if that is equals to `perm` var
                    # IMPORTANT: by using this, it will easily filter permissions available, and if there were none, then it is automatically false
                    q.select(0, q.filter_(lambda i: q.equals(perm, i),
                                          q.select(self.permissions_field,
                                                   q.select("data",
                                                            q.get(q.match(
                                                                q.index(
                                                                    self.get_relation_index_name()),
                                                                q.current_identity(),
                                                                group_ref
                                                            )))))),
                    perm
                )
            )
        )


# class GenericUserBasedRoleM2M(GenericAuthorizationRole):
#     """ Generic set of permissions for many-to-many entity to user relationship """

#     def get_name_suffix(self):
#         # TODO: return suffix:
#         return f'{self.get_group_table().lower()}_based_crud_role'

#     def get_relation_index_name(self):
#         # TODO: return index name: `users_blogs_by_blog_and_newuser`
#         """ Returns the index name of the m2m index of group and user e.g. 'users_groups_by_group_and_user' """
#         user_col = self.get_user_collection()
#         user_groups = user_col._base_properties.get("groups")
#         group_table = self.get_group_table().lower()
#         if group_table:
#             relation_index_name = (user_groups.relation_name
#                                    + '_by_'
#                                    + group_table
#                                    + '_and_'
#                                    + self.get_user_table().lower())
#             return relation_index_name
#         return None

#     def get_lambda(self, resource_type):
#         # TODO: refactor to look for the M2M index and see if the user has permission for the entity
#         current_user_field = self.collection.get_user_field()
#         if resource_type == 'write':
#             lambda_args = ["old_object", "new_object", "object_ref"]
#             user_ref = q.select(current_user_field,
#                                 q.select('data', q.var('old_object')))
#             return q.query(
#                 q.lambda_(lambda_args,
#                           q.and_(
#                               q.equals(
#                                   user_ref,
#                                   q.current_identity()
#                               ),
#                               q.equals(
#                                   q.select(current_user_field, q.select(
#                                       'data', q.var('new_object'))),
#                                   q.current_identity()
#                               )
#                           )

#                           )
#             )
#         elif resource_type == 'create':
#             lambda_args = ["new_object"]
#             user_ref = q.select(current_user_field,
#                                 q.select('data', q.var('new_object')))
#         elif resource_type == 'read' or resource_type == 'delete':
#             lambda_args = ["object_ref"]
#             user_ref = q.select(current_user_field,
#                                 q.select('data', q.get(q.var('object_ref'))))

#         return q.query(
#             q.lambda_(lambda_args,
#                       q.equals(
#                           user_ref,
#                           q.current_identity()
#                       )
#                       )
#         )
