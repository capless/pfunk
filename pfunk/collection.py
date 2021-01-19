from valley.schema import BaseSchema
from valley.declarative import DeclaredVars, DeclarativeVariablesMetaclass
from faunadb import query as q
from .fields import BaseField


class PFunkDeclaredVars(DeclaredVars):
    base_field_class = BaseField


class PFunkDeclarativeVariablesMetaclass(DeclarativeVariablesMetaclass):
    declared_vars_class = PFunkDeclaredVars


class Collection(BaseSchema, metaclass=PFunkDeclarativeVariablesMetaclass):
    """
    Base class for all pFunk Documents classes.
    """
    BUILTIN_DOC_ATTRS = ('_id',)

    def add_index(self, index):
        pass

    def get_collection_name(self):
        return self.get_class_name().capitalize()

    @classmethod
    def create(cls, **kwargs):
        c = cls(**kwargs)
        c.validate()
        resp = cls.Meta.handler["client"].query(
            q.create(
                q.collection(c.get_collection_name()),
                {
                    "data": c._data
                }
            ))
        c.ref = resp['ref']
        return c

    def save(self):
        self.validate()

        # Create Collection if it does not exist
        if not self.Meta.handler["client"].query(q.exists(q.collection(self.get_collection_name()))):
            self.Meta.handler["client"].query(q.create_collection(
                {"name": self.get_collection_name()}))

        if not self.ref:
            resp = self.Meta.handler["client"].query(
                q.create(
                    q.collection(self.get_collection_name()),
                    {
                        "data": self._data
                    }
                ))
            self.ref = resp['ref']
        else:
            self.Meta.handler["client"].query(
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
        resp = cls.Meta.handler["client"].query(
            q.get(q.ref(q.collection(c.get_collection_name()), ref)))
        ref = resp['ref']
        data = resp['data']

        obj = c.__class__(**data)
        obj.ref = ref
        return obj

    def delete(self):
        self.Meta.handler["client"].query(q.delete(self.ref))

    class Meta:
        handler = None

# class UDF(object):

#     def update(self):
#         client.query(
#             q.update(q.function(self.name), {
#                 "body": q.query(
#                     q.lambda_("input",
#                               self.get_input()

#                               )
#                 )
#             })
#         )

#     def get_input(self):
#         return q.count(
#             q.filter_(
#                 q.lambda_("doc",
#                           q.equals(
#                               q.select(["data", "status"],
#                                        q.get(q.var("doc"))),
#                               "repair"
#                           )
#                           ),
#                 q.match(
#                     q.index("dealer_vehicles_by_dealer"),
#                     q.select(["data", "dealership"], q.get(q.identity()))
#                 )
#             )
#         )
