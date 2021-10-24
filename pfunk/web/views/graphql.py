import requests
from envs import env
from werkzeug.routing import Rule

from pfunk.exceptions import GraphQLError
from pfunk.utils.publishing import BearerAuth
from pfunk.web.response import GraphQLResponse
from pfunk.web.views.json import JSONView
from graphql.parser import GraphQLParser
from graphql.exceptions import SyntaxError as GQLSyntaxError

parser = GraphQLParser()


class GQL(object):

    def __init__(self, body):
        """ Converts query to a workable python object that
            works with pfunk 
        
        Args:
            body (dict, required):
                The whole graphql query
        """
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        self.body = body
        self.parsed = parser.parse(self.body)
        self.doc = self.parsed.definitions[0]
        self.type = self.doc.__class__.__name__.lower()
        self.name = self.doc.selections[0].name
        if self.type == 'query':
            self.process_query()
        elif self.type == 'mutation':
            self.process_mutation()

    def process_query(self):
        """ Acquire the fields in a graphql query  """
        self.fields = [i.name for i in self.doc.selections[0].selections[0].selections]

    def process_mutation(self):
        """ Acquire the values in a mutation query """
        self.fields = self.doc.selections[0].arguments[0].value


class GraphQLView(JSONView):
    """ Creates a GraphQL view. 
    
        Utilizes Fauna's builtin graphql endpoint.
    """
    login_required = True
    http_methods = ['post']
    response_class = GraphQLResponse

    def get_query(self):
        gql = self.process_graphql()
        resp = requests.request(
                method='post',
                url=env('FAUNA_GRAPHQL_URL', 'https://graphql.fauna.com/graphql'),
                json=self.request.get_json(),
                auth=BearerAuth(self.request.token),
                allow_redirects=False
            )
        return resp.json()

    def process_graphql(self):
        """ Transform request to a workable Graphql query """
        body = self.request.get_json().get('query')
        if not body:
            body = self.request.body
        try:
            return GQL(body)
        except GQLSyntaxError as e:
            raise GraphQLError(e)

    @classmethod
    def url(cls, collection=None):
        return Rule(f'/graphql/', endpoint=cls.as_view(),
                    methods=cls.http_methods)