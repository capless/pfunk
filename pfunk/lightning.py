from faunadb.client import FaunaClient
from faunadb import query as q
from .collection import Collection


class PFunk:

    def __init__(self, key):
        self.client = FaunaClient(key)

        if self.client.query(q.exists(q.collection("PFUNK_META"))):
            # TODO: GET PFUNK_META
            pass
        else:
            # TODO: CREATE PFUNK_META
            self.client.query(q.create_collection(
                {"name": "PFUNK_META"}))

    def add_collection(self, collection):
        if not issubclass(collection, Collection):
            raise TypeError('Input parameter is not of type: Collection')
        if issubclass(collection, Collection) and collection not in self._collection_list:
            self._collection_list.append(collection)
            cl = set(self._collection_list)
            self._collection_list = list(cl)

    def add_index(self, index):
        pass

    def _modify_meta(self, **data):
        pass
