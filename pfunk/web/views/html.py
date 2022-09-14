from pfunk.client import q
from pfunk.utils.templates import temp_env
from pfunk.web.response import Response, HttpNotFoundResponse, HttpBadRequestResponse, HttpMethodNotAllowedResponse, \
    HttpUnauthorizedResponse, HttpForbiddenResponse
from pfunk.web.views.base import UpdateMixin, ActionMixin, IDMixin, ObjectMixin, QuerysetMixin, RESTView


class HTMLView(RESTView):
    """
    Base class for all HTML views
    """
    response_class = Response
    content_type_accepted = 'text/html'
    restrict_content_type = False
    not_found_class = HttpNotFoundResponse
    bad_request_class = HttpBadRequestResponse
    method_not_allowed_class = HttpMethodNotAllowedResponse
    unauthorized_class = HttpUnauthorizedResponse
    forbidden_class = HttpForbiddenResponse
    template_name = None

    def get_template(self):
        return temp_env.get_template(
            self.template_name.format(
                collection=self.collection.get_collection_name().lower(),
                action=self.action
            )
        )

    def get_response(self):
        return self.response_class(
            payload=self.get_template().render(**self.get_context()),
            headers=self.get_headers()
        )


class HTMLCreateView(UpdateMixin, ActionMixin, HTMLView):
    """
    Define a `Create` view that allows `creation` of an entity in the collection
    """
    action = 'create'
    http_methods = ['post']
    login_required = True

    def get_query(self):
        """ Entity created in a collection """
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


class HTMLUpdateView(UpdateMixin, IDMixin, HTMLView):
    """
    Define a view to allow `Update` operations
    """
    action = 'update'
    http_methods = ['put']
    login_required = True

    def get_query(self):
        """ Entity updated in a collection """
        obj = self.collection.update(**self.get_query_kwargs(), _token=self.request.token)
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
                    data={
                        '_class': col.get_class_name(),
                        '_ref': obj['_ref']
                    }
                )
            )


class HTMLDetailView(ObjectMixin, IDMixin, HTMLView):
    """ Define a view to allow single entity operations """
    action = 'detail'
    restrict_content_type = False
    login_required = True

    def get_context(self):
        """ Context for the view """
        context = super(HTMLDetailView, self).get_context()
        context['object'] = self.get_query()
        return context


class HTMLDeleteView(ObjectMixin, IDMixin, HTMLView):
    """ Define a view to allow `Delete` entity operations """
    action = 'delete'
    http_methods = ['delete']
    login_required = True

    def get_query(self):
        """ Deleted an entity in the specified collection """
        return self.collection.delete_from_id(self.request.kwargs.get('id'), _token=self.request.token)

    def get_context(self):
        """ Context for the view """
        context = super(HTMLDeleteView, self).get_context()
        context['object'] = self.get_query()
        return context

class HTMLListView(QuerysetMixin, ActionMixin, HTMLView):
    """ Define a view to allow `All/List` entity operations """
    restrict_content_type = False
    action = 'list'
    login_required = True

    def get_context(self):
        """ Context for the view """
        context = super(HTMLListView, self).get_context()
        context['object_list'] = self.get_query()
        return context