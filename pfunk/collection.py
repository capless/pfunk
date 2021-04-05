from valley.schema import BaseSchema
from valley.declarative import DeclaredVars, DeclarativeVariablesMetaclass
from .loading import q
from .fields import BaseField


class PFunkDeclaredVars(DeclaredVars):
    base_field_class = BaseField


class PFunkDeclarativeVariablesMetaclass(DeclarativeVariablesMetaclass):
    declared_vars_class = PFunkDeclaredVars


class Enum(list):
    name = None
    
    
class Collection(BaseSchema, metaclass=PFunkDeclarativeVariablesMetaclass):
    """
    Base class for all pFunk Documents classes.
    """
    BUILTIN_DOC_ATTRS = ('_id',)

    def add_index(self, index):
        pass

    def get_collection_name(self):
        return self.get_class_name().capitalize()

    @property
    def client(self):
        if self._client:
            return self._client
        self._client = self.Meta.handler.get_client(self.Meta.db_label)
        return self._client

    @classmethod
    def create(cls, _credentials=None, **kwargs):
        c = cls(**kwargs)
        data_dict = {
            "data": c._data
        }
        if _credentials and isinstance(_credentials, dict):
            data_dict['credentials'] = _credentials
        c.validate()
        resp = c.client.query(
            q.create(
                q.collection(c.get_collection_name()),
                data_dict
            ))
        c.ref = resp['ref']
        return c

    def save(self):
        self.validate()
        if not self.ref:
            resp = self.client.query(
                q.create(
                    q.collection(self.get_collection_name()),
                    {
                        "data": self._data
                    }
                ))
            self.ref = resp['ref']
        else:
            self.client.query(
                q.update(
                    self.ref,
                    {
                        "data": self._data
                    }
                )
            )

    @classmethod
    def get(cls, ref):
        c = cls()
        resp = c.client.query(q.get(q.ref(q.collection(c.get_collection_name()), ref)))
        ref = resp['ref']
        data = resp['data']

        obj = c.__class__(**data)
        obj.ref = ref
        return obj

    def delete(self):
        self.client.query(q.delete(self.ref))


class UDF(object):

    def update(self):
        self.client.query(
            q.update(q.function(self.name), {
                "body": q.query(
                    q.lambda_("input",
                              self.get_input()

                              )
                )
            })
        )

    def get_input(self):
        return q.count(
            q.filter_(
                q.lambda_("doc",
                          q.equals(
                              q.select(["data", "status"], q.get(q.var("doc"))),
                              "repair"
                          )
                          ),
                q.match(
                    q.index("dealer_vehicles_by_dealer"),
                    q.select(["data", "dealership"], q.get(q.identity()))
                )
            )
        )