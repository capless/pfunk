from valley.utils import import_util

from pfunk.client import q
from pfunk.web.response import JSONResponse, JSONNotFoundResponse, JSONBadRequestResponse, \
    JSONMethodNotAllowedResponse, JSONUnauthorizedResponse, JSONForbiddenResponse
from pfunk.web.views.base import HTTPView, ObjectMixin, QuerysetMixin, UpdateMixin, \
    JSONActionMixin, JSONIDMixin


class JSONView(HTTPView):
    """ Creates a view that accepts & returns json 
    
        Uses the various JSON responses defined in 
        `pfunk.web.response`
    """
    response_class = JSONResponse
    content_type_accepted = 'application/json'
    restrict_content_type = True
    not_found_class = JSONNotFoundResponse
    bad_request_class = JSONBadRequestResponse
    method_not_allowed_class = JSONMethodNotAllowedResponse
    unauthorized_class: JSONUnauthorizedResponse = JSONUnauthorizedResponse
    forbidden_class = JSONForbiddenResponse

    def get_response(self):
        return self.response_class(
            payload=self.get_query(),
            headers=self.get_headers()
        )


class CreateView(UpdateMixin, JSONActionMixin, JSONView):
    """ Define a `Create` view that allows `creation` of an entity in the collection """
    action = 'create'
    http_methods = ['post']
    login_required = True

    def get_query(self):
        """ Entity created in a collection """
        data = self.get_query_kwargs()
        fields = self.collection.get_foreign_fields_by_type('pfunk.fields.ManyToManyField')
        for k, v in fields.items():
            col = import_util(v['foreign_class'])
            entities = []
            for ref in data[k]:
                c = col.get(ref)

                # # TODO: instantiate collection by just passsing the ref
                # col_data = {'_ref': ref}
                # c = col(**col_data)
                # # print(f'\n\nCOLLECTION AND REF {c.get_collection_name()} -> {ref}\n\n')
                # # c._ref = q.ref(q.collection(c.get_collection_name()), ref)
                # # print(f'\n\nCOLLECTION ID: {c._id}\n\n')
                # print(f'\n\nCOLLECTION REF ID: {c.ref}\n\n')
                entities.append(c)
            data[k] = entities
        obj = self.collection.create(**data, _token=self.request.token)
        return obj


class UpdateView(UpdateMixin, JSONIDMixin, JSONView):
    """ Define a view to allow `Update` operations """
    action = 'update'
    http_methods = ['put']
    login_required = True

    def get_query(self):
        """ Entity in collection updated by an ID """
        data = self.get_query_kwargs()
        obj = self.collection.get(self.request.kwargs.get('id'), _token=self.request.token)
        fields = self.collection.get_foreign_fields_by_type('pfunk.fields.ManyToManyField')
        for k, v in fields.items():
            col = import_util(v['foreign_class'])
            entities = []
            for ref in data[k]:
                c = col.get(ref)

                # # TODO: instantiate collection by just passsing the ref
                # col_data = {'_ref': ref}
                # c = col(**col_data)
                # # print(f'\n\nCOLLECTION AND REF {c.get_collection_name()} -> {ref}\n\n')
                # # c._ref = q.ref(q.collection(c.get_collection_name()), ref)
                # # print(f'\n\nCOLLECTION ID: {c._id}\n\n')
                # print(f'\n\nCOLLECTION REF ID: {c.ref}\n\n')
                entities.append(c)
            data[k] = entities

        obj._data.update(data)
        obj.save()
        return obj


class DetailView(ObjectMixin, JSONIDMixin, JSONView):
    """ Define a view to allow single entity operations """
    action = 'detail'
    restrict_content_type = False
    login_required = True


class DeleteView(ObjectMixin, JSONIDMixin, JSONView):
    """ Define a view to allow `Delete` entity operations """
    action = 'delete'
    http_methods = ['delete']
    login_required = True

    def get_query(self):
        """ Deleted an entity in the specified collection """
        return self.collection.delete_from_id(self.request.kwargs.get('id'), _token=self.request.token)


class ListView(QuerysetMixin, JSONActionMixin, JSONView):
    """ Define a view to allow `All/List` entity operations """
    restrict_content_type = False
    action = 'list'
    login_required = True
