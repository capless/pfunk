from envs import env

from pfunk.collection import Collection
from pfunk.fields import SlugField, ManyToManyField, StringField


class Group(Collection):
    """ Group collection that the user belongs to """
    name = StringField(required=True)
    slug = SlugField(unique=True, required=False)
    users = ManyToManyField(
        env('USER_COLLECTION', 'pfunk.contrib.auth.collections.user.User'),
        relation_name='users_groups')

    def __unicode__(self):
        return self.name  # pragma: no cover
