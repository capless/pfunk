from pfunk import StringField, Collection, DateTimeField, Enum, EnumField
from pfunk.contrib.auth.resources import CreateUser, LoginUser, UpdatePassword, Public
from pfunk.contrib.generic import GenericDelete
from pfunk.fields import EmailField, SlugField, ManyToManyField
from pfunk.client import q


AccountStatus = Enum(name='AccountStatus', choices=['ACTIVE', 'INACTIVE'])


class Group(Collection):
    name = StringField(required=True)
    slug = SlugField(unique=True, required=False)
    users = ManyToManyField('pfunk.contrib.auth.collections.User', relation_name='users_groups')

    def __unicode__(self):
        return self.name


class BaseUser(Collection):
    _credential_field = 'password'
    _functions = [LoginUser, UpdatePassword]
    _crud_functions = [CreateUser, GenericDelete]
    _roles = [Public]
    username = StringField(required=True, unique=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    email = EmailField(required=True, unique=True)
    account_status = EnumField(AccountStatus, required=True, default_value="INACTIVE")

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
        c = cls(**kwargs)
        c.validate()
        u = c.client.query(
            q.call("create_user", kwargs)
        )
        c.ref = u.get('data').get('ref')
        return c

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

    def get_identity(self):
        return self.client.query(
            q.get(q.current_identity())
        )

    def __unicode__(self):
        return self.username


class User(BaseUser):
    groups = ManyToManyField(Group, 'users_groups')


