import datetime

import pytz

from pfunk import StringField, Collection, DateTimeField, Enum, EnumField
from pfunk.contrib.auth.resources import CreateUser, LoginUser, UpdatePassword, Public
from pfunk.fields import EmailField
from pfunk.client import q


AccountStatus = Enum(name='AccountStatus', choices=['ACTIVE', 'INACTIVE'])


class User(Collection):
    _credential_field = 'password'
    _functions = [LoginUser, UpdatePassword, CreateUser]
    _roles = [Public]
    username = StringField(required=True, unique=True)
    email = EmailField(required=True, unique=True)
    account_status = EnumField(AccountStatus, required=True, default_value="INACTIVE")
    last_login = DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.username

    @classmethod
    def login(cls, username, password):
        c = cls()
        return c.client.query(
            q.call("login_user", {"username": username, "password": password})
        )

    @classmethod
    def create_user(cls, **kwargs):
        c = cls()
        kwargs['last_login'] = datetime.datetime.now(tz=pytz.UTC)
        return c.client.query(
            q.call("create_user", kwargs)
        )

    @classmethod
    def update_password(cls, current_password, new_password):
        c = cls()
        return c.client.query(
            q.call("update_password", {'current_password': current_password, 'new_password': new_password})
        )

    def update_password_b(self, current_password, new_password):
        self.client.query(
        q.if_(q.identify(self.get_identity(),
                         current_password),
              q.update(q.current_identity(), {
                  "credentials": {"password": new_password}
              }),
              q.abort("Wrong current password.")
              ))

    def get_user_fields(self):
        return {k: q.select(k, q.var("input")) for k,v in self._base_properties.items() if k != 'last_login'}

    def get_identity(self):
        return self.client.query(
            q.current_identity()
        )

    def __unicode__(self):
        return self.username


