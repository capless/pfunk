from valley.exceptions import ValidationException
from valley.schema import BaseSchema
from valley.declarative import DeclaredVars, DeclarativeVariablesMetaclass

from pfaunk.fields import BaseField


class PFaunkDeclaredVars(DeclaredVars):
    base_field_class = BaseField


class PFaunkDeclarativeVariablesMetaclass(DeclarativeVariablesMetaclass):
    declared_vars_class = PFaunkDeclaredVars


class Collection(BaseSchema, metaclass=PFaunkDeclarativeVariablesMetaclass):
    """
    Base class for all Docb Documents classes.
    """
    BUILTIN_DOC_ATTRS = ('_id',)

    def add_index(self, index):
        pass


class Enum(list):

    def __init__(self, *args, **kwargs):
        self.enum_name = kwargs.pop('name')
        if not self.enum_name:
            raise ValueError('Enum requires name keyword argument.')
        super(Enum, self).__init__(*args, **kwargs)


class Index(object):
    pass