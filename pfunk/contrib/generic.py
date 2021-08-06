from pfunk.resources import Function, Index
from pfunk.client import q



class GenericFunction(Function):
    action = 'create'

    def get_role(self):
        return None # pragma: no cover

    def get_name(self):
        return f"{self.action}_{self.collection.get_class_name()}"

    def get_fields(self):
        return self.collection.get_fields()


class AllFunction(GenericFunction):

    def get_name(self):
        return self.collection.all_function_name()

    def get_body(self):
        return q.query(
            q.lambda_(["input"],
                q.map_(
                    q.lambda_(['ref'],
                        q.get(q.var('ref'))
                    ),
                    q.paginate(
                        q.match(q.index(self.collection.all_index_name())),
                        q.select('size', q.var('input'))
                    )
                )
            )
        )
    
    
class GenericCreate(GenericFunction):

    def get_body(self):
        data_dict = {
            "data": self.get_fields(),
        }
        return q.query(
            q.lambda_(["input"],
                      q.create(
                          q.collection(self.collection.get_collection_name()),
                          data_dict
                      )
                      ))


class GenericUpdate(GenericFunction):
    action = 'update'

    def get_body(self):
        data_dict = {
            "data": self.get_fields(),
        }
        return q.query(
            q.lambda_(["input"],
                      q.update(
                          q.collection(self.collection.get_collection_name(), q.select('id', q.var("input"))),
                          data_dict
                      )
                      ))



class GenericDelete(GenericFunction):
    action = 'delete'

    def get_body(self):
        return q.query(
            q.lambda_(["input"],
                      q.delete(q.ref(q.collection(self.collection.get_collection_name()), q.select('id', q.var("input"))))
                      )
        )