from pfunk import StringField, Collection, DateTimeField, Enum, EnumField
from pfunk.contrib.auth.resources import CreateUser, LoginUser, UpdatePassword, Public, UserRole
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
    _roles = [Public, UserRole]
    _non_public_fields = ['groups']
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
    def get_from_id(cls):
        c = cls()
        ref = c.client.query(
            q.current_identity()
        )
        return cls(_ref=ref, _lazied=True)

    @classmethod
    def create_user(cls, **kwargs):

        c = cls(**kwargs)

        c.validate()
        password = kwargs.pop('password')
        data = c.get_create_user_values()
        data['password'] = password

        u = c.client.query(
            q.call("create_user", data)
        )

        return

    def get_create_user_values(self):
        data = dict()
        for k, v in self._data.items():
            prop = self._base_properties.get(k)
            data[k] = prop.get_db_value(value=v)
        return data

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


