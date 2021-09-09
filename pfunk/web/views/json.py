from pfunk.web.response import JSONResponse, JSONNotFoundResponse, JSONBadRequestResponse, \
    JSONMethodNotAllowedResponse, JSONUnauthorizedResponse, JSONForbiddenResponse
from pfunk.client import q
from pfunk.web.views.base import ActionMixin, HTTPView, IDMixin, ObjectMixin, QuerysetMixin, UpdateMixin


class JSONView(HTTPView):
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
    action = 'create'
    http_methods = ['put']
    login_required = True

    def get_query(self):
        obj = self.collection.create(**self.get_query_kwargs(), _token=self.request.token)
        return obj

    def get_m2m_kwargs(self, obj):
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
    action = 'update'
    http_methods = ['post']
    login_required = True

    def get_query(self):
        obj = self.collection.get(self.request.kwargs.get('id'), _token=self.request.token)
        obj._data.update(self.get_query_kwargs())
        obj.save()
        return obj


class DetailView(ObjectMixin, IDMixin, JSONView):
    action = 'detail'
    restrict_content_type = False
    login_required = True


class DeleteView(ObjectMixin, IDMixin, JSONView):
    action = 'delete'
    http_methods = ['delete']
    login_required = True

    def get_query(self):
        return self.collection.delete_from_id(self.request.kwargs.get('id'), _token=self.request.token,
                                              **self.get_query_kwargs())


class ListView(QuerysetMixin, ActionMixin, JSONView):
    restrict_content_type = False
    action = 'list'
    login_required = True


class GraphQLView(HTTPView):
    pass