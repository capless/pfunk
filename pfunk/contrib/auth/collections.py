from pfunk import StringField, Collection, DateTimeField


class BaseUser(Collection):
    username = StringField(required=True)
    password = StringField(required=True)
    last_login = DateTimeField(auto_now=True)

    def login(self, username, password):
        pass

    def __unicode__(self):
        return self.username


class BaseUserAPIKey(BaseUser):
    api_key = StringField(required=True)