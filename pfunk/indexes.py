from valley.contrib import Schema
from valley.properties import CharProperty, BooleanProperty, ForeignProperty, ForeignListProperty


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

    def render(self):
        pass

    def __init__(self):
        i = IndexSchema(name=self.name, source=self.source, terms=self.terms, values=self.values,
                        serialized=self.serialized, unique=self.unique)
        i.validate()

    def get_kwargs(self):
        kwargs = {'name': self.name, 'source': q.collection(self.source), 'serialized': self.serialized,
                  'unique': self.unique}
        if self.terms:
            kwargs['terms'] = self.terms.render()
        if self.values:
            kwargs['values'] = self.values.render()
        return kwargs

    def publish(self):
        return client.query(q.create_index(self.get_kwargs()))