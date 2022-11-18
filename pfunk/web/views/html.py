from pfunk.client import q
from pfunk.forms.collections import CollectionForm
from pfunk.utils.templates import temp_env
from pfunk.web.response import Response, HttpNotFoundResponse, HttpBadRequestResponse, HttpMethodNotAllowedResponse, \
    HttpUnauthorizedResponse, HttpForbiddenResponse, HttpRedirectResponse
from pfunk.web.views.base import UpdateMixin, ActionMixin, IDMixin, ObjectMixin, QuerysetMixin, HTTPView


class HTMLView(HTTPView):
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


class FormMixin(UpdateMixin):
    success_url = '/{collection}/{action}/'

    def get_form(self, form_class=None):
        """ Acquires the form for the request """
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def get_data(self):
        return self.request.form_data

    def get_object(self):
        """ Acquires the object for the request """
        return self.collection.get(self.request.kwargs.get('id'))

    def get_context(self):
        context = super(UpdateMixin, self).get_context()
        context['form'] = self.get_form()
        return context

    def get_form_class(self):
        """ Acquires or builds the form class to use for updating the object """
        if self.form_class:
            return self.form_class
        return self.build_form_class()

    def build_form_class(self):
        """ Builds the form class to use for updating the object """

        class Meta:
            collection = self.collection

        form_class = type(f"{self.collection.get_collection_name()}Form", (CollectionForm,), {
            # constructor

            "Meta": Meta,
        })
        return form_class

    def get_form_kwargs(self):
        """ Acquires the kwargs for the form """
        data = self.request.form_data
        if self.action == 'update':
            if not data:
                data = dict()
            data['_instance'] = self.get_object()
        return data

    def form_valid(self, form):
        """ Called when the form is valid """
        q = self.get_query()
        return HttpRedirectResponse(
            location=self.get_success_url(),
        )

    def get_success_url(self):
        """ Acquires the success url for the form """
        return self.success_url.format(
            collection=self.collection.get_collection_name().lower(),
            action='list')

    def form_invalid(self, form):
        """ Called when the form is invalid """
        print(self.action, "Form Invalid: Got Here")
        return self.error_response(form._errors)

    def get_response(self, form=None):
        if self.request.method == 'POST':
            form = self.get_form()
            form.validate()
            if form._is_valid:
                return self.form_valid(form)
        return self.response_class(
            payload=self.get_template().render(**self.get_context()),
            headers=self.get_headers()
        )

    def get_m2m_kwargs(self, obj):
        """ Acquires the keyword-arguments for the many-to-many relationship

        FaunaDB is only able to create a many-to-many relationship
        by creating a collection that references both of the object.
        So, when creating an entity, it is needed to create an entity to
        make them related to each other.

        Args:
            obj (dict, required):

        """
        data = self.get_data()
        fields = self.collection.get_foreign_fields_by_type('pfunk.fields.ManyToManyField')
        for k, v in fields.items():
            current_value = data.get(k)
            col = v.get('foreign_class')()
            client = col().client()
            client.query(
                q.create(

                )
            )


class HTMLCreateView(FormMixin, ActionMixin, HTMLView):
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


class HTMLUpdateView(FormMixin, IDMixin, HTMLView):
    """
    Define a view to allow `Update` operations
    """
    action = 'update'
    http_methods = ['post']
    login_required = True

    def get_query(self):
        obj = self.collection.get(self.request.kwargs.get('id'), _token=self.request.token)
        kwargs = self.get_query_kwargs()
        try:
            kwargs.pop('_instance')
        except KeyError:
            pass
        obj._data.update(kwargs)
        obj.save()
        return obj


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
    http_methods = ['get', 'post']
    login_required = True
    success_url = '/{collection}/{action}/'

    def get_query(self):
        """ Deleted an entity in the specified collection """
        return self.collection.delete_from_id(self.request.kwargs.get('id'), _token=self.request.token)

    def get_object(self):
        """ Acquires the object for the request """
        return self.collection.get(self.request.kwargs.get('id'), _token=self.request.token)

    def get_context(self):
        """ Context for the view """
        context = super(HTMLDeleteView, self).get_context()
        context['object'] = self.get_object()
        return context

    def get_success_url(self):
        """ Acquires the success url for the form """
        return self.success_url.format(
            collection=self.collection.get_collection_name().lower(),
            action='list')

    def post(self, **kwargs):
        self.get_query()
        return HttpRedirectResponse(
            location=self.get_success_url(),
        )


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
