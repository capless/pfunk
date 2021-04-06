import datetime

import pytz
from valley.properties import CharProperty, IntegerProperty, DateTimeProperty, DateProperty, FloatProperty, \
    BooleanProperty, EmailProperty, SlugProperty, BaseProperty, ForeignProperty

from pfunk.collection import Enum


class GraphQLMixin(object):
    GRAPHQL_FIELD_TYPE = 'String'

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
        super(EnumField, self).__init__(default_value, required, validators, choices, verbose_name, **kwargs)
        self.enum = enum

        if not isinstance(self.enum, Enum):
            raise ValueError('The first argument of an EnumField should be an Enum')
        self.choices = self.enum.choices

    def get_graphql_type(self):
        self.unique = self.kwargs.get('unique')
        self.index_name = self.kwargs.get('index_name')
        req = ''
        unique = ''
        if self.required:
            req = '!'
        if self.unique:
            unique = '@unique'
        return f"{self.enum.name}{req} {unique}"


class ReferenceField(GraphQLMixin, ForeignProperty):

    def get_db_value(self, value):
        return value._ref


class DateField(GraphQLMixin, DateProperty):
    GRAPHQL_FIELD_TYPE = 'Date'

    def now(self):
        return datetime.datetime.now(tz=pytz.UTC).date()
