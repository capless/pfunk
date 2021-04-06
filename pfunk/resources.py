import re
from pfunk.utils.publishing import create_or_update_function, create_or_update_role


class Resource(object):
    name = None

    def __init__(self, collection):
        self.collection = collection

    @classmethod
    def get_name(cls):
        return cls.name or re.sub('(?!^)([A-Z]+)', r'_\1', cls.__name__).lower()

    def get_payload(self):
        return {
            'name': self.get_name(),
            'body': self.get_body()
        }

    def publish(self):
        raise NotImplementedError

    def get_body(self):
        raise NotImplementedError


class Function(Resource):

    def publish(self):
        return create_or_update_function(self.collection.client, self.get_payload())


class Role(Resource):

    def publish(self):
        return create_or_update_role(self.collection.client, self.get_payload())