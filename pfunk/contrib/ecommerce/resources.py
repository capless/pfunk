from pfunk.client import q
from pfunk.contrib.auth.resources import GenericGroupBasedRole, GenericUserBasedRole, Public, UserRole


class StripePublic(Public):

    def get_privileges(self):
        privs = super().get_privileges()
        privs.append(
            {
                "resource": q.collection(self.collection.get_collection_name()),
                "actions": {
                    'read': self.get_lambda('read')
                }
            }
        )
        return privs
