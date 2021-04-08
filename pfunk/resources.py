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

    def get_membership(self):
        return {
            'resource': q.collection(self.collection.get_collection_name())
        }


    def publish(self):
        return create_or_update_role(self.collection.client, self.get_payload())