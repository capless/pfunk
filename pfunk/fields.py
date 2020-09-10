from valley.properties import BaseProperty

from pfunk.mixins import (CharVariableMixin, IntegerVariableMixin, DateTimeMixin, FloatVariableMixin, DateMixin,
                          BooleanMixin)


class BaseField(BaseProperty):
    GRAPHQL_FIELD_TYPE = 'String'

    def __init__(self, default_value=None,
                 required=False,
                 index=False,
                 index_name=None,
                 unique=False,
                 validators=[],
                 verbose_name=None,
                 **kwargs
                 ):
        super(BaseField, self).__init__(
            default_value=default_value,
            required=required,
            index=index,
            index_name=index_name,
            unique=unique,
            validators=validators,
            verbose_name=verbose_name,
            **kwargs
        )
        self.index = index
        self.index_name = index_name

    def get_graphql_type(self):
        return self.GRAPHQL_FIELD_TYPE


class StringField(CharVariableMixin, BaseField):
    pass


class IntegerField(IntegerVariableMixin, BaseField):
    GRAPHQL_FIELD_TYPE = 'Int'


class DateTimeField(DateTimeMixin, BaseField):
    GRAPHQL_FIELD_TYPE = 'Time'

    def __init__(
            self,
            default_value=None,
            required=True,
            validators=[],
            verbose_name=None,
            auto_now=False,
            auto_now_add=False,
            **kwargs):

        super(
            DateTimeField,
            self).__init__(
            default_value=default_value,
            required=required,
            validators=validators,
            verbose_name=verbose_name,
            **kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add


class FloatField(FloatVariableMixin, BaseField):
    GRAPHQL_FIELD_TYPE = 'Float'


class BooleanField(BooleanMixin, BaseField):
    GRAPHQL_FIELD_TYPE = 'Boolean'


class DateField(DateMixin, BaseField):
    GRAPHQL_FIELD_TYPE = 'Date'

    def __init__(
            self,
            default_value=None,
            required=True,
            validators=[],
            verbose_name=None,
            auto_now=False,
            auto_now_add=False,
            **kwargs):

        super(
            DateField,
            self).__init__(
            default_value=default_value,
            required=required,
            validators=validators,
            verbose_name=verbose_name,
            **kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add