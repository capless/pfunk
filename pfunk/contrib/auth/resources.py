from valley.utils import import_util
from tokenize import group
from envs import env

from pfunk.client import q
from pfunk.resources import Function, Role

# Global collections
# USER_CLASS = env('USER_COLLECTION', 'User')
# GROUP_CLASS = env('GROUP_COLLECTION', 'Group')


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
    """This class provides generic authorization roles for collections"""

    def get_relation_index_name(self) -> str:
        """
        Returns the index name of the created permission index of group and user -> 'usergroups_by_userID_and_groupID'
        """
        return 'usergroups_by_userID_and_groupID'

    def get_user_table(self) -> str:
        """Returns the user table name"""
        return self.collection.user_collection or env('USER_COLLECTION', 'User')

    def get_group_table(self) -> str:
        """Returns the group table name"""
        return self.collection.group_collection or env('GROUP_COLLECTION', 'Group')

    def get_name_suffix(self) -> str:
        """Returns the name suffix for this role"""
        return f'{self.collection.get_user_field().lower()}_based_crud_role'

    def get_name(self) -> str:
        """Returns the name for this role"""
        return self.name or f"{self.collection.get_class_name()}_{self.get_name_suffix()}"

    def get_privileges(self) -> list:
        """Returns the list of privileges for this role"""
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
    """Class to provide a generic set of permissions based on the user-entity relationship. 

    Args:
        GenericAuthorizationRole (class): Inherited class 
    """

    def get_relation_index_name(self):
        """Returns the user-group by user index name 

        Formatted as: {user_group_relation_name}_by_{user_class}

        Returns:
            str: User-group by user index name
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
        """ Returns the lambda for the specified resource type 

        Args:
            resource_type (str): Type of resource  

        Returns:
            q.query: Lambda query
        """
        current_user_field = self.collection.get_user_field()
        if resource_type == 'write':
            lambda_args = ["old_object", "new_object", "object_ref"]
            user_ref = q.select(
                current_user_field, q.select('data', q.var('old_object')))
            return q.query(
                q.lambda_(
                    lambda_args,
                    q.and_(
                        q.equals(user_ref, q.current_identity()),
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
            user_ref = q.select(
                current_user_field, q.select('data', q.var('new_object')))
        elif resource_type == 'read' or resource_type == 'delete':
            lambda_args = ["object_ref"]
            user_ref = q.select(
                current_user_field, q.select('data', q.get(q.var('object_ref'))))

        return q.query(
            q.lambda_(lambda_args, q.equals(user_ref, q.current_identity()))
        )

class GenericGroupBasedRole(GenericAuthorizationRole):
    """Class for giving permissions to Group-based entities
    """
    # Initialize the `permissions_field` variable
    permissions_field = 'permissions'

    def get_name_suffix(self):
        """Get the name suffix for the group-based role

        Returns:
            str: The name suffix for the group-based role
        """
        return f'{self.get_group_table().lower()}_based_crud_role'
    
    def get_lambda(self, resource_type):
        """Returns the lambda function for giving the permission to Group-based entities 
        
        Args:
            resource_type (str): The type of operation (create, read, write, and delete)
        
        Returns:
            Lambda: The lambda function for giving the permission to Group-based entities 
        """
        current_group_field = self.collection.get_group_field().lower()
        perm = f'{self.collection.get_collection_name()}-{resource_type}'.lower()

        # Initialize the lambda arguments based on the `resource_type`
        if resource_type == 'write':
            group_ref = q.select(current_group_field,
                                 q.select('data', q.var('old_object')))
            lambda_args = ["old_object", "new_object", "object_ref"]
        elif resource_type == 'create':
            lambda_args = ["new_object"]
            group_ref = q.select(current_group_field,
                                 q.select('data', q.var('new_object')))
        elif resource_type == 'read' or resource_type == 'delete':
            lambda_args = ["object_ref"]
            group_ref = q.select(current_group_field,
                                 q.select('data', q.get(q.var('object_ref'))))

        if resource_type == 'write':
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
        else:
            # Return the lambda function for giving the permission to Group-based entities 
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


class GenericUserBasedRoleM2M(GenericAuthorizationRole):
    """ Generic set of permissions for many-to-many entity to user relationship """

    def get_privileges(self):
        """
        Usage of parent `get_privileges()` with addition of access to M2M collection
        Returns:
            List: list of privileges
        """
        priv_list = super().get_privileges()
        fields = self.collection.get_foreign_fields_by_type('pfunk.fields.ManyToManyField')
        for field, value in fields.items():
            # Get foreign column
            foreign_col = self.collection._base_properties.get(field)
            relation_name = foreign_col.relation_name
            if relation_name:
                priv_list.extend([
                    {
                        "resource": q.collection(relation_name),
                        "actions": {
                            'read': True,
                            'create': True,
                            'update': False,
                            'delete': False
                        }
                    }
                ])
        return priv_list

    def get_name_suffix(self):
        """
        Returns:
            String: suffix for name of the role
        """
        return f'{self.collection.get_user_field().lower()}_based_crud_role'

    def get_relation_index_name(self):
        """
        Returns the index name of the m2m index of an entity and user e.g. 'users_blogs_by_blog_and_newuser'
        Returns:
            String: name of the index
        """
        user_field = self.collection.get_user_field()
        if user_field:
            user_field = user_field.lower()
        else:
            return None
        user_col = self.collection._base_properties.get(user_field)
        user_col_relation = user_col.relation_name

        group_table = self.get_group_table().lower()
        if group_table:
            relation_index_name = (user_col_relation
                                   + '_by_'
                                   + self.collection.get_collection_name().lower()
                                   + '_and_'
                                   + self.get_user_table().lower())
            return relation_index_name
        return None

    def get_lambda(self, resource_type):
        """
        Returns lamda expression for the given resource type
        Args:
            resource_type (String): type of resource
        Returns:
            Lamda expression
        """
        current_user_field = self.collection.get_user_field()
        if resource_type == 'write':
            lambda_args = ["old_object", "new_object", "object_ref"]
            obj_ref = q.var('old_object')
            return q.query(
                q.lambda_(lambda_args,
                    q.and_(
                        q.equals(
                            q.select(f'{self.get_user_table().lower()}ID',
                                     q.select("data",
                                              q.get(q.match(
                                                  q.index(
                                                      self.get_relation_index_name()),
                                                  obj_ref,
                                                  q.current_identity()
                                              )))
                                     ),
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
            # Create ops will always be allowed 
            return True
        elif resource_type == 'read' or resource_type == 'delete':
            lambda_args = ["object_ref"]
            obj_ref = q.var('object_ref')

        return q.query(
            q.lambda_(
                lambda_args,
                q.equals(
                    q.select(f'{self.get_user_table().lower()}ID',
                             q.select("data",
                                      q.get(q.match(
                                          q.index(
                                              self.get_relation_index_name()),
                                          obj_ref,
                                          q.current_identity()
                                      )))
                             ),
                    q.current_identity()
                )
            )
        )