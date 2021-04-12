import re
from pfunk.utils.publishing import create_or_update_function, create_or_update_role
from pfunk.client import q
from valley.contrib import Schema
from valley.properties import CharProperty, BooleanProperty, ForeignProperty, ForeignListProperty


class Resource(object):
    name = None

    def __init__(self, collection):
        self.collection = collection

    def get_name(self):
        return self.name or re.sub('(?!^)([A-Z]+)', r'_\1', self.__class__.__name__).lower()

    def get_payload(self):
        payload_dict =  {
            'name': self.get_name(),
            'body': self.get_body()
        }
        role = self.get_role()
        if role:
            payload_dict['role'] = role
        return payload_dict

    def publish(self):
        raise NotImplementedError

    def get_body(self):
        raise NotImplementedError


class Function(Resource):

    def get_role(self):
        return None

    def publish(self):
        return create_or_update_function(self.collection.client, self.get_payload())


class Role(Resource):
    user_table = None

    def get_lambda(self, resource_type):
        return

    def get_payload(self):
        payload_dict = {
            "name": self.get_name(),
            "membership": self.get_membership(),
            "privileges": self.get_privileges(),
        }
        data = self.get_data()
        if data:
            payload_dict['data'] = data
        return payload_dict

    def get_data(self):
        return None

    def get_privileges(self):
        raise NotImplementedError

    def get_membership_lambda(self):
        return q.query(
            q.lambda_(['object_ref'],
                q.equals(
                    q.select('account_status', q.select('data', q.get(q.var('object_ref')))),
                    "ACTIVE"
                )
                      ))

    def get_membership(self):
        return {
            'resource': q.collection(self.user_table or self.collection.get_collection_name()),
            'predicate': self.get_membership_lambda()
        }

    def publish(self):
        return create_or_update_role(self.collection.client, self.get_payload())


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