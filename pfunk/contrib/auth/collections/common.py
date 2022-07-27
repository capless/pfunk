from envs import env

from pfunk import ReferenceField, Collection
from pfunk.fields import ListField


class UserGroups(Collection):
    """ Many-to-many collection of the user-group relationship

        The native fauna-way of holding many-to-many relationship
        is to only have the ID of the 2 object. Here in pfunk, we
        leverage the flexibility of the collection to have another
        field, which is `permissions`, this field holds the capablities
        of a user, allowing us to add easier permission handling.
        Instead of manually going to roles and adding individual
        collections which can be painful in long term.

    Attributes:
        collection_name (str):
            Name of the collection in Fauna
        userID (str):
            Fauna ref of user that is tied to the group
        groupID (str):
            Fauna ref of a collection that is tied with the user
        permissions (str[]):
            List of permissions, `['create', 'read', 'delete', 'write']`
    """
    collection_name = 'users_groups'
    userID = ReferenceField(env('USER_COLLECTION', 'pfunk.contrib.auth.collections.user.User'))
    groupID = ReferenceField(env('GROUP_COLLECTION', 'pfunk.contrib.auth.collections.group.Group'))
    permissions = ListField()

    def __unicode__(self):
        return f"{self.userID}, {self.groupID}, {self.permissions}"
