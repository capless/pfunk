from valley.contrib import Schema
from valley.properties import CharProperty, BooleanProperty, ForeignProperty, ForeignListProperty
from .client import q


class TermValueField(Schema):
    name = CharProperty(required=True)
    reverse = BooleanProperty(default_value=True)


class Binding(Schema):
    name = CharProperty(required=True)


class TermValue(Schema):
    bindings = ForeignListProperty(Binding, required=False)
    fields = ForeignListProperty(TermValueField, required=False)

    def render(self):
        obj_list = []
        if self.bindings:
            binding_list = [{"binding": i.name} for i in self.bindings]
            obj_list.extend(binding_list)
        if self.fields:
            field_list = [{'field': ['data', i.name], 'reverse': i.reverse} for i in self.fields]
            obj_list.extend(field_list)
        return obj_list


class IndexSchema(Schema):
    name = CharProperty(required=True)
    source = CharProperty(required=True)
    terms = ForeignProperty(TermValue, required=False)
    values = ForeignProperty(TermValue, required=False)
    serialized = BooleanProperty(default_value=True)
    unique = BooleanProperty(default_value=False)


class Index(object):
    name = None
    source = None
    unique = False
    serialized = True
    terms = None
    values = None

    def __init__(self, collection):
        i = IndexSchema(name=self.name, source=self.source, terms=self.terms, values=self.values,
                        serialized=self.serialized, unique=self.unique)
        i.validate()
        self.collection = collection

    def get_kwargs(self):
        kwargs = {'name': self.name, 'source': q.collection(self.source), 'serialized': self.serialized,
                  'unique': self.unique}
        if self.terms:
            kwargs['terms'] = self.terms.render()
        if self.values:
            kwargs['values'] = self.values.render()
        return kwargs

    def publish(self):
        return self.collection.client.query(q.create_index(self.get_kwargs()))