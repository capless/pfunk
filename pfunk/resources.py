import re

from pfunk.utils.publishing import create_or_update_function, create_or_update_role
from pfunk.client import q


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


class Index(object):
    name = None
    source = None
    unique = False
    serialized = True
    terms = None
    values = None
    _accept_kwargs = ['name', 'source', 'unique', 'serialized', 'terms', 'values']

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if k in self._accept_kwargs:
                setattr(self, k, v)

    def get_kwargs(self):
        kwargs = {'name': self.name, 'source': q.collection(self.source), 'serialized': self.serialized,
                  'unique': self.unique}
        if self.terms:
            kwargs['terms'] = self.terms
        if self.values:
            kwargs['values'] = self.values
        return kwargs

    def publish(self, client):
        return client.query(q.create_index(self.get_kwargs()))