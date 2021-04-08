from pfunk.resources import Function
from pfunk.client import q


class Generic(Function):
    action = 'create'

    def get_role(self):
        return 'admin'

    def get_name(self):
        return f"{self.action}_{self.collection.get_class_name()}"


class GenericCreate(Function):

    def get_body(self):
        data_dict = {
            "data": self.collection.get_fields(),
        }
        return q.query(
            q.lambda_(["input"],
                      q.create(
                          q.collection(self.collection.get_collection_name()),
                          data_dict
                      )
                      ))


class GenericUpdate(Generic):
    action = 'update'

    def get_body(self):
        data_dict = {
            "data": self.collection.get_fields(),
        }
        return q.query(
            q.lambda_(["input"],
                      q.update(
                          q.collection(self.collection.get_collection_name(), q.select('id', q.var("input"))),
                          data_dict
                      )
                      ))



class GenericDelete(Generic):
    action = 'delete'

    def get_body(self):
        return q.query(
            q.lambda_(["input"],
                      q.delete(q.ref(q.collection(self.collection.get_collection_name()), q.select('id', q.var("input"))))
                      )
        )