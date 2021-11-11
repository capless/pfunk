from authlib.oauth2.rfc6749 import ClientMixin
from authlib.oauth2.rfc6749 import TokenMixin

from pfunk.fields import StringField, IntegerField, DateTimeField, ReferenceField
from pfunk.collection import Collection
from pfunk.contrib.auth.collections import User as PFunkUser


class Client(Collection, ClientMixin):
    """ Model for registering `Clients` to allow connection """
    id = StringField(unique=True, required=True)
    user = ReferenceField(PFunkUser)


class Token(Collection, TokenMixin):
    """ Token class collection """
    pass
