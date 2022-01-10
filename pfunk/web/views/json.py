from pfunk.web.response import JSONResponse, JSONNotFoundResponse, JSONBadRequestResponse, \
    JSONMethodNotAllowedResponse, JSONUnauthorizedResponse, JSONForbiddenResponse
from pfunk.client import q
from pfunk.web.views.base import ActionMixin, HTTPView, IDMixin, ObjectMixin, QuerysetMixin, UpdateMixin


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


class CreateView(UpdateMixin, ActionMixin, JSONView):
    """ Define a `Create` view that allows `creation` of an entity in the collection """
    action = 'create'
    http_methods = ['post']
    login_required = True

    def get_query(self):
        obj = self.collection.create(**self.get_query_kwargs(), _token=self.request.token)
        return obj

    def get_m2m_kwargs(self, obj):
        """ Acquires the keyword-arguments for the many-to-many relationship 
        
        FaunaDB is only able to create a many-to-many relationship
        by creating a collection that references both of the object. 
        So, when creating an entity, it is needed to create an entity to
        make them related to each other.

        Args:
            obj (dict, required):

        """
        data = self.request.get_json()
        fields = self.collection.get_foreign_fields_by_type('pfunk.fields.ManyToManyField')
        for k, v in fields.items():
            current_value = data.get(k)
            col = v.get('foreign_class')()
            client = col().client()
            client.query(
                q.create(

                )
            )


class UpdateView(UpdateMixin, IDMixin, JSONView):
    """ Define a view to allow `Update` operations """
    action = 'update'
    http_methods = ['put']
    login_required = True

    def get_query(self):
        obj = self.collection.get(self.request.kwargs.get('id'), _token=self.request.token)
        obj._data.update(self.get_query_kwargs())
        obj.save()
        return obj


class DetailView(ObjectMixin, IDMixin, JSONView):
    """ Define a view to allow single entity operations """
    action = 'detail'
    restrict_content_type = False
    login_required = True


class DeleteView(ObjectMixin, IDMixin, JSONView):
    """ Define a view to allow `Delete` entity operations """
    action = 'delete'
    http_methods = ['delete']
    login_required = True

    def get_query(self):
        return self.collection.delete_from_id(self.request.kwargs.get('id'), _token=self.request.token)


class ListView(QuerysetMixin, ActionMixin, JSONView):
    """ Define a view to allow `All/List` entity operations """
    restrict_content_type = False
    action = 'list'
    login_required = True


class GraphQLView(HTTPView):
    pass