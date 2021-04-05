import datetime

import pytz

from pfunk import StringField, Collection, DateTimeField
from pfunk.loading import q, Ref
from pfunk.utils.publishing import create_or_update_function


class User(Collection):
    _credential_field = 'password'
    username = StringField(required=True, unique=True)
    account_status = StringField(required=True, default_value="INACTIVE", choices=["ACTIVE", "INACTIVE"])
    last_login = DateTimeField(auto_now=True)

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

    def publish_function_create_user(self):
        data_dict = {
            "data": self.get_user_fields(),
            "credentials": {
                self._credential_field: q.select(self._credential_field, q.var("input"))
            }
        }
        payload = {
                "name": "create_user",
                "body": q.query(
                    q.lambda_(["input"],
                    q.create(
                        q.collection(self.get_collection_name()),
                        data_dict

            )
            ))
            }
        create_or_update_function(self.client, payload)

    def publish_function_update_password(self):
        payload = {
                "name": "update_password",
                "body": q.query(q.lambda_(["input"],
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
            }
        create_or_update_function(self.client, payload)

    def publish_function_login_user(self):
        payload = {
                "name": "login_user",
                "body": q.query(
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
            }
        create_or_update_function(self.client, payload)

    def get_user_fields(self):
        return {k: q.select(k, q.var("input")) for k,v in self._base_properties.items() if k != 'last_login'}

    @classmethod
    def publish_functions(cls):
        c = cls()
        c.publish_function_login_user()
        c.publish_function_create_user()
        c.publish_function_update_password()

    def __unicode__(self):
        return self.username