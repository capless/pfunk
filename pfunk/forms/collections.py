from valley.utils import import_util

from pfunk.forms.form import Form


class CollectionForm(Form):
    _template = 'forms/ul.html'

    def __init__(self, **kwargs):
        try:
            self._instance = kwargs.pop('_instance')
        except KeyError:
            self._instance = None
        if self._instance:
            self._data = self._instance.to_dict(flat=True).get('data')
        self.create_fields()
        super(CollectionForm, self).__init__(**kwargs)

    @classmethod
    def add_field_choices(cls, class_name, field):
        if class_name == 'EnumField':
            choices = {item: item for item in field.choices}
        else:
            choices = {str(obj): obj.ref.id() for obj in cls.get_queryset(
                field.get_foreign_class(), field.choices_index)}
        return choices

    @classmethod
    def get_queryset(cls, collection, index=None):
        if not index:
            return collection.all()
        return collection.get_index(index)

    def add_field(self, name, field):
        # We need to know the class name to determine the correct form field
        class_name = field.__class__.__name__
        # We use the class name to get the correct form field class from the map
        field_class = import_util(field.get_form_field())

        if field_class:
            field_kwargs = {
                'required': field.required,
            }
            if field.choices:
                field_kwargs['choices'] = field.choices
            if class_name in ['ReferenceField', 'ManyToManyField', 'EnumField']:
                field_kwargs['choices'] = self.add_field_choices(
                    class_name, field)
            if field.default_value:
                field_kwargs['default_value'] = field.default
            try:
                if self._data.get(name):
                    field_kwargs['value'] = self._data.get(name)
            except AttributeError:
                pass
            self._base_properties[name] = field_class(**field_kwargs)

    def create_fields(self):
        if hasattr(self.Meta, 'fields') and len(self.Meta.fields) > 0:
            for name in self.Meta.fields:
                self.add_field(name, self.Meta.collection._base_properties[name])
        else:
            try:
                for name, field in self.Meta.collection._base_properties.items():
                    self.add_field(name, field)
            except TypeError:
                pass

    def save(self):
        return self.Meta.collection(**self._data).save()

    class Meta:
        collection = None
        fields = None
