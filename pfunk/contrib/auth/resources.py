from pfunk.resources import Function, Role
from pfunk.client import q


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
                    q.create(
                        q.collection(self.collection.get_collection_name()),
                        data_dict

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
                    "resource": q.function("create_user"),
                    "actions": {
                        "call": True
                        }
                },
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
                }


            ]


class GenericGroupBasedRole(Role):
    relation_index_name = 'users_groups_by_group_and_user'
    through_user_field = 'userID'
    current_group_field = 'group'
    user_table = 'User'

    def get_name(self):
        return f"{self.collection.get_class_name()}_crud_role"

    def get_lambda(self, resource_type):
        if resource_type == 'write':
            group_ref = q.select(self.current_group_field,
                     q.select('data', q.get(q.var('new_object_ref'))))
            lambda_args = ["old_object_ref", "new_object_ref"]
        elif resource_type == 'read':
            group_ref = q.select(self.current_group_field,
                     q.select('data', q.get(q.var('object_ref'))))
            lambda_args = ["object_ref"]
        return q.query(
                            q.lambda_(lambda_args,
                                q.exists(
                                    #User ID from index
                                    q.select(self.through_user_field,
                                        q.select("data",
                                            q.get(
                                                q.match(
                                                    q.index(self.relation_index_name),
                                                    group_ref,
                                                    q.current_identity()
                                                )
                                            )))

                                )
                            )
                        )

    def get_privileges(self):
        return [
            {
              "resource": q.collection(self.collection.get_collection_name()),
              "actions": {
                  'read': self.get_lambda('read'),
                  'write': self.get_lambda('write'),
                  'create': self.get_lambda('write'),
                  'delete': self.get_lambda('read'),
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
            {
                "resource": q.function(f'create_{self.collection.get_class_name()}'),
                "actions": {
                    "call": True
                }
            },
            {
                "resource": q.function(f'update_{self.collection.get_class_name()}'),
                "actions": {
                    "call": True
                }
            },
            {
                "resource": q.function(f'delete_{self.collection.get_class_name()}'),
                "actions": {
                    "call": True
                }
            }
        ]