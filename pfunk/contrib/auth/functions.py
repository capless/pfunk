from pfunk.functions import Function
from pfunk.loading import q


class LoginUser(Function):

    def get_body(self):
        return q.query(
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


class UpdatePassword(Function):

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


class CreateUser(Function):

    def get_body(self):

        data_dict = {
            "data": self.collection.get_user_fields(),
            "credentials": {
                self.collection._credential_field: q.select(self.collection._credential_field, q.var("input"))
            }
        }
        return q.query(
                    q.lambda_(["input"],
                    q.create(
                        q.collection(self.collection.get_collection_name()),
                        data_dict

            )
            ))