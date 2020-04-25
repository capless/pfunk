from valley.properties import BaseProperty

from pfaunk.mixins import CharVariableMixin, IntegerVariableMixin


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