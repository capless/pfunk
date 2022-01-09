import re

from faunadb.query import query

from pfunk.utils.publishing import create_or_update_function, create_or_update_role, create_or_pass_index
from pfunk.client import q


class Resource(object):
    """
    Resource class is the base class for Function, Role, and Index class.
    """
    name: str = None

    def __init__(self, collection):
        """

        Args:
            collection: Collection class
        """

        self.collection = collection

    def get_name(self) -> str:
        """
        Returns the name of the resource

        Returns: str
        """
        return self.name or re.sub('(?!^)([A-Z]+)', r'_\1', self.__class__.__name__).lower()

    def get_role(self):
        """
        Returns the role

        Returns: str or None
        """
        return None

    def get_payload(self) -> dict:
        """
        Returns the payload to create the resource.

        Returns: dict
        """
        payload_dict = {
            'name': self.get_name(),
            'body': self.get_body(),
            'role': self.get_role()
        }

        return payload_dict

    def publish(self):
        raise NotImplementedError # pragma: no cover

    def unpublish(self):
        raise NotImplementedError # pragma: no cover

    def get_body(self):
        raise NotImplementedError # pragma: no cover


class Function(Resource):

    def get_role(self):
        """Gets the role to use when calling the function."""
        return None # pragma: no cover

    def publish(self):
        """
        Publish the function

        Returns: Fauna response
        """
        return create_or_update_function(self.collection.client(), self.get_payload())

    def unpublish(self):
        """
        Unpublish the function

        Returns: Fauna response
        """
        return self.collection.client().query(q.delete(q.function(self.name)))


class Role(Resource):
    user_table: str = None

    def get_lambda(self, resource_type):
        return # pragma: no cover

    def get_payload(self) -> dict:
        """
        Returns the payload to create the role.

        Returns: dict
        """
        payload_dict = {
            "name": self.get_name(),
            "membership": self.get_membership(),
            "privileges": self.get_privileges(),
        }
        data = self.get_data()
        if data:
            payload_dict['data'] = data
        return payload_dict

    def get_data(self) -> dict:
        """
        Defines user-defined metadata for the role. It is provided for the developer to store role-relevant information.

        Returns: dict
        """
        return None # pragma: no cover

    def get_privileges(self):
        raise NotImplementedError # pragma: no cover

    def get_membership_lambda(self):
        """
        Defines predicate function for membership in a role.

        Returns: Fauna query
        """
        return q.query(
            q.lambda_(['object_ref'],
                q.equals(
                    q.select('account_status', q.select('data', q.get(q.var('object_ref')))),
                    "ACTIVE"
                )
                      ))

    def get_membership(self) -> dict:
        """
        Returns the membership configuration for the role

        Returns: dict
        """
        return {
            'resource': q.collection(self.user_table or self.collection.get_collection_name()),
            'predicate': self.get_membership_lambda()
        }

    def publish(self):
        """
        Publish role

        Returns: Fauna Response
        """
        return create_or_update_role(self.collection.client(), self.get_payload())

    def unpublish(self):
        """
        Unpublish role

        Returns: Fauna Response
        """
        return self.collection.client().query(q.delete(q.role(self.name)))


class Index(object):
    name: str = None
    source: str = None
    unique: bool = None
    serialized: bool = None
    terms: list = None
    values: list = None
    _accept_kwargs: list = ['name', 'source', 'unique', 'serialized', 'terms', 'values']

    def __init__(self, **kwargs):
        """
        Creates the Index instance
        Args:
            **kwargs: If the keyword argument is in the _accept_kwargs list then it will override the class variable of
            the same name.
        """
        for k, v in kwargs.items():
            if k in self._accept_kwargs:
                setattr(self, k, v)

    def get_kwargs(self) -> dict:
        """
        Returns the keyword arguments for creating the index just before the call is made to Fauna.

        Returns: dict

        """

        kwargs = {'name': self.name, 'source': q.collection(self.source), }
        if self.terms:

            kwargs['terms'] = self.terms
        if self.values:
            kwargs['values'] = self.values
        if self.serialized:
            kwargs['serialized'] = self.serialized
        if self.unique:
            kwargs['unique'] = self.unique

        return kwargs

    def get_name(self) -> str:
        """
        Returns the name of the index.

        Returns: str

        """
        return self.name

    def publish(self, client) -> query:
        """
        Publish the index to Fauna
        Args:
            client: FaunaClient instance

        Returns: query

        """
        return create_or_pass_index(client, self.get_kwargs())

    def unpublish(self, client) -> query:
        """
        Unpublish Index
        Returns: query

        """
        return client.query(q.delete(q.index(self.name)))


class Filter(Function):
    indexes: list = []

    def get_body(self):
        return q.query(
            q.lambda_(["input"],
                      q.map_(
                          q.lambda_(['ref'],
                                    q.get(q.var('ref'))
                                    ),
                          q.paginate(
                              q.match(q.index(self.collection.all_index_name())),
                              q.select('size', q.var('input'))
                          )
                      )
                      )
        )

