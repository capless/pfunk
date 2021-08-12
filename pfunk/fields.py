import datetime

import pytz
from valley.exceptions import ValidationException
from valley.properties import CharProperty, IntegerProperty, DateTimeProperty, DateProperty, FloatProperty, \
    BooleanProperty, EmailProperty, SlugProperty, BaseProperty, ForeignProperty, ForeignListProperty, ListProperty
from valley.utils import import_util

from valley.validators import Validator, ChoiceValidator, ForeignValidator

from pfunk.collection import Enum
from pfunk.client import Ref


class ChoiceListValidator(ChoiceValidator):

    def validate(self, value, key):
        if value:
            if not value in self.choices:
                raise ValidationException(f'{value}: This value is outside of values set for {key}')


class GraphQLMixin(object):
    GRAPHQL_FIELD_TYPE = 'String'
    relation_field = False

    def get_foreign_class(self):
        if isinstance(self.foreign_class, str):
            return import_util(self.foreign_class)
        return self.foreign_class

    def get_graphql_type(self):
        self.unique = self.kwargs.get('unique')
        self.index_name = self.kwargs.get('index_name')
        req = ''
        unique = ''
        if self.required:
            req = '!'
        if self.unique:
            unique = '@unique'

        return f"{self.GRAPHQL_FIELD_TYPE}{req} {unique}"


class StringField(GraphQLMixin, CharProperty):
    pass


class IntegerField(GraphQLMixin, IntegerProperty):
    GRAPHQL_FIELD_TYPE = 'Int'


class DateTimeField(GraphQLMixin, DateTimeProperty):
    GRAPHQL_FIELD_TYPE = 'Time'

    def now(self):
        return datetime.datetime.now(tz=pytz.UTC)


class FloatField(GraphQLMixin, FloatProperty):
    GRAPHQL_FIELD_TYPE = 'Float'


class BooleanField(GraphQLMixin, BooleanProperty):
    GRAPHQL_FIELD_TYPE = 'Boolean'


class EmailField(GraphQLMixin, EmailProperty):
    pass


class SlugField(GraphQLMixin, SlugProperty):
    pass


class EnumField(GraphQLMixin, BaseProperty):

    def __init__(
            self,
            enum,
            default_value=None,
            required=False,
            validators=[],
            choices=None,
            verbose_name=None,
            **kwargs
    ):
        self.enum = enum
        if not isinstance(self.enum, Enum):
            raise ValueError('The first argument of an EnumField should be an Enum')
        validators = [ChoiceListValidator(self.enum.choices)]
        super(EnumField, self).__init__(default_value, required, validators, choices, verbose_name, **kwargs)
        self.choices = self.enum.choices

    def get_graphql_type(self):
        super(EnumField, self).get_graphql_type()
        req = ''
        unique = ''
        if self.required:
            req = '!'
        if self.unique:
            unique = '@unique'
        return f"{self.enum.name}{req} {unique}"


class ReferenceValidator(ForeignValidator):

    def validate(self, value, key):
        if isinstance(self.foreign_class, str):
            self.foreign_class = import_util(self.foreign_class)
        if value:
            if not isinstance(value, self.foreign_class):
                raise ValidationException('{0}: This value ({1}) should be an instance of {2}.'.format(
                    key, value, self.foreign_class.__name__))

class ReferenceField(GraphQLMixin, ForeignProperty):

    def get_validators(self):
        super(BaseProperty, self).get_validators()
        self.validators.insert(0, ReferenceValidator(self.foreign_class))

    def get_graphql_type(self):
        super(ReferenceField, self).get_graphql_type()
        req = ''
        unique = ''
        if self.required:
            req = '!'
        if self.unique:
            unique = '@unique'
        return f"{self.get_foreign_class().__name__}{req} {unique}"

    def get_python_value(self, value):
        if value and isinstance(value, Ref):
            try:
                i = self.foreign_class()
            except TypeError:
                i = import_util(self.foreign_class)()
            i.ref = value
            i._lazied = True
            return i
        return value

    def get_db_value(self, value):
        if value:
            return value.ref
        return value


class ManyToManyValidators(ForeignValidator):

    def validate(self, value, key):
        if isinstance(self.foreign_class, str):
            self.foreign_class = import_util(self.foreign_class)
        if value:
            for obj in value:
                if not isinstance(obj,self.foreign_class):
                    raise ValidationException(
                        '{0}: This value ({1}) should be an instance of {2}.'.format(
                            key, obj, self.foreign_class.__name__))


class ManyToManyField(GraphQLMixin, ForeignListProperty):
    relation_field = True

    def __init__(self, foreign_class, relation_name, return_type=None,return_prop=None,**kwargs):
        self.foreign_class = foreign_class
        self.relation_name = relation_name
        super(ManyToManyField, self).__init__(foreign_class, return_type=return_type, return_prop=return_prop, **kwargs)

    def get_validators(self):
        return [ManyToManyValidators(self.foreign_class)]

    def get_graphql_type(self):
        super(ManyToManyField, self).get_graphql_type()
        req = ''
        if self.required:
            req = '!'
        return f'[{self.get_foreign_class().__name__}{req}] @relation(name: "{self.relation_name}")'

    def get_python_value(self, value):
        ref_list = []
        ra = ref_list.append
        if isinstance(value, list):
            for i in value:
                if isinstance(i, Ref):
                    c = self.foreign_class()
                    c.ref = i
                    c._lazied = True
                    ra(c)
                if isinstance(i, self.foreign_class):
                    ra(i)
        return ref_list

    def get_db_value(self, value):
        if isinstance(value, list):
            return [i.ref for i in value if hasattr(i, 'ref')]
        else:
            return None


class DateField(GraphQLMixin, DateProperty):
    GRAPHQL_FIELD_TYPE = 'Date'

    def now(self):
        return datetime.datetime.now(tz=pytz.UTC).date()


class ListField(GraphQLMixin, ListProperty):
    GRAPHQL_FIELD_TYPE = '[String]'

    def get_db_value(self, value):
        return value


class ForeignList(ForeignListProperty):
    def get_validators(self):
        return [ManyToManyValidators(self.foreign_class)]
