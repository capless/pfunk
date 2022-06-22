import os
import re
import json
import swaggyp as sw
from werkzeug.routing import Map, parse_rule

from pfunk.collection import Collection

GRAPHQL_TO_YAML_TYPES = {
    "String": "string",
    "Int": "integer",
    "Float": "integer",
    "Boolean": "boolean"
}

PFUNK_TO_YAML_TYPES = {
    "StringField": "string",
    "SlugField": "string",
    "EmailField": "string",
    "EnumField": "string",
    "ManyToManyField": "#/definitions/",
    "ReferenceField": "#/definitions/",
    "ForeignList": "#/definitions/",
    "IntegerField": "integer",
    "FloatField": "integer",
    "BooleanField": "boolean",
    "ListField": "array"
}

WERKZEUG_URL_TO_YAML_TYPES = {
    "int": "integer",
    "string": "string",
    "float": "integer",
    "path": "string",
    "uuid": "string"
}


class SwaggerDoc(object):

    def __init__(self, collections, rules=[], config_file='pfunk.json'):
        """ Generates swagger doc. Details are going to be acquired from the collections 
        
            The acquisition of the information needed for docs are as follows:
            ```
                Response: 
                    Description (str): View's `get_query` docstrings
                    Status Code (int): 
                        Acquired from `response_class` class variable of a view
                        Error status_codes are acquired too in class variables
                Operation:
                    HTTP Methods (arr): Defined `http_methods` in a view.
                    Summary (str): ({http_method}) -> {collection_name}
                    Description (str): Docstring of the view
                Path:
                    Endpoint (str): Path of the function. You can see it in `url` method of a view.
                Model:
                    Name (str): The class name of the `collection`
                    Properties (str): The fields of the collection and their type
            ```

            Args:
                collections ([`pfunk.collection.Collection`]):
                    array of collection of the project to generate models from
                rules ([`werkzeug.routing.Rule`]):
                    array of additional URLs that the given collection doesn't have
                config_file (str, optional):
                    directory of the config_file

            Returns:
                swagger.yaml (yaml, required):
                    Generated YAML file
        """
        self.collections = collections
        self.rules = rules
        self.paths = []
        self.definitions = []
        self.responses = []
        self.config_file = config_file
        self._response_classes = [
            'response_class',
            'not_found_class',
            'bad_request_class',
            'method_not_allowed_class',
            'unauthorized_class',
            'forbidden_class'
        ]

    def _convert_url_to_swagger(self, replacement: str, to_replace: str) -> str:
        return re.sub('<\w+:\w+>', f'{{{replacement}}}', to_replace)

    def write_to_yaml(self, dir=''):
        """ Using the class' variables, write it to a swagger (yaml) file 
        
            It will create `swagger.yaml` file in current directory, if 
            there is already one, it will print the yaml file instead.

            Args:
                dir (str, optional):
                    custom directory of the swagger file. If there are no provided, create one in current dir.
            Returns:
                dir (str, required):
                    directory of the created swagger file
                swagger_file (str, required):
                    the contents of the swagger yaml file
        """
        if not os.path.exists(self.config_file):
           raise Exception('Missing JSON Config file.')
        else:
            with open(self.config_file, 'r') as f:
                data = json.loads(f.read())
                proj_title = data.get('name')
                proj_desc = data.get('description', 'A Pfunk project')
                proj_ver = data.get('ver', '1.0')
                host = data.get('host', 'pfunk.com')
                basePath = data.get('basePath', '/')
                schemes = ['https']

        if dir:
            if not dir.endswith('/'):
                dir = dir + "/"

        info = sw.Info(
            title=proj_title,
            description=proj_desc,
            version=proj_ver)
        t = sw.SwaggerTemplate(
            host=host,
            basePath=basePath,
            info=info,
            paths=self.paths,
            schemes=schemes,
            definitions=self.definitions)

        if not os.path.exists(f'{dir}swagger.yaml'):
            with open(f'{dir}swagger.yaml', 'x') as swag_doc:
                swag_doc.write(t.to_yaml())
        else:
            print(
                'There is an existing swagger file. Kindly move/delete it to generate a new one.')
            # print(t.to_yaml())
        return {
            "dir": f'{dir}swagger.yaml',
            "swagger_file": t.to_yaml()
        }

    def get_operations(self, col: Collection):
        """ Acquires all of the endpoint in the collections and make it 
            as an `operation` for swagger doc

            Appends all of the acquired paths here in `self.paths` 
            array class variable
 
        Args:
            col (`pfunk.collection.Collection`, required): 
                The collection that has views
        
        Returns:
            paths ([`swaggyp.Path`], required):
                An array of `Path` that can be consumed using 
                `swaggyp.SwaggerTemplate` to show 
                available paths 
        ```
        """
        for view in col.collection_views:
            route = view.url(col)
            rule = route.rule
            methods = route.methods
            args = route.arguments
            arg_type = None
            responses = []
            for rsp_cls in self._response_classes:
                if rsp_cls == 'response_class':
                    responses.append(
                        sw.Response(
                            status_code=view.response_class.status_code,
                            description=view.get_query.__doc__ or 'Fill the docstrings to show description')
                    )
                else:
                    responses.append(
                        sw.Response(
                            status_code=getattr(view, rsp_cls).status_code,
                            description=getattr(view, rsp_cls).default_payload)
                    )

            view_methods = list(methods)
            for method in view_methods:
                if method == 'HEAD':
                    # Skip HEAD operations
                    continue

                # Acquire path parameters of URL
                if args is None or len(args) == 0:
                    # if `defaults` weren't used in URL building, use the argument defined in the URL string
                    for converter, arguments, variable in parse_rule(rule):
                        if variable.startswith('/') or converter is None:
                            continue
                        args = variable
                        arg_type = converter

                params = []
                # Construct path parameters for swagger generation
                if arg_type:
                    path_params = sw.Parameter(
                        name=args,
                        _type=WERKZEUG_URL_TO_YAML_TYPES.get(arg_type),
                        _in='path',
                        description='',
                        required=True,
                        allowEmptyValue=False
                    )
                    params.append(path_params)

                # Acquire payload of the view from the View's `_payload_docs`
                view_payload = view()._payload_docs()

                # Construct payload for swagger generation
                if view_payload:
                    for field in view_payload.get('data'):
                        if field.get('schema'):
                            schema = sw.SwagSchema(ref=field.get('schema'))
                            param = sw.Parameter(
                                    name=field.get('name'),
                                    _in=field.get('in'),
                                    description=field.get('description'),
                                    required=field.get('required'),
                                    schema=schema
                                )
                        else:
                            param = sw.Parameter(
                                name=field.get('name'),
                                _type=field.get('type'),
                                _in=field.get('in'),
                                description=field.get('description'),
                                required=field.get('required'),
                                allowEmptyValue=False
                            )
                        params.append(param)

                consumes = ['application/json',
                            'application/x-www-form-urlencoded']
                produces = ['application/json',
                            'application/x-www-form-urlencoded']
                view_docs = view.__doc__
                if params:
                    op = sw.Operation(
                        http_method=method.lower(),
                        summary=f'({method}) -> {col.__class__.__name__}',
                        description=view_docs,
                        responses=responses,
                        consumes=consumes,
                        produces=produces,
                        parameters=params)
                else:
                    op = sw.Operation(
                        http_method=method.lower(),
                        summary=f'({method}) -> {col.__class__.__name__}',
                        description=view_docs,
                        responses=responses,
                        consumes=consumes,
                        produces=produces)

                # Replace werkzeug params (<int: id>) to swagger-style params ({id})
                swagger_rule = self._convert_url_to_swagger(args, rule)
                p = sw.Path(endpoint=swagger_rule, operations=[op])
                self.paths.append(p)
        return self.paths

    def get_model_definitions(self, col: Collection):
        """ Acquires collection's name, fields, and relationships to
            convert it to a swagger `Definition` 

            Converts `ReferenceField` and `ManyToManyField` to 
            reference other definitions as a characterization
            of relationships defined on models
            
        Args:
            col (`pfunk.collection.Collection`, required): 
                The collection that has views
        
        Returns:
            definitions ([`swaggyp.Definition`], required):
                An array of `Definition` that can be consumed using 
                `swaggyp.SwaggerTemplate` to show 
                available models 

        Payload:

        
        """
        # Define model definitions by iterating through collection's fields for its properties
        col_properties = {}
        for property, field_type in col._base_properties.items():
            # Get pfunk field specifier
            field_type_class = field_type.__class__.__name__

            if field_type_class in ['ReferenceField', 'ManyToManyField']:
                # Acquire the class that the collection is referencing to
                foreign_class = field_type.get_foreign_class().__name__
                ref_field = PFUNK_TO_YAML_TYPES.get(field_type_class)
                col_properties[property] = {
                    "$ref": ref_field + foreign_class}
            else:
                col_properties[property] = {
                    "type": PFUNK_TO_YAML_TYPES.get(field_type_class)}
        model_schema = sw.SwagSchema(properties=col_properties)
        model = sw.Definition(name=type(col).__name__, schema=model_schema)
        self.definitions.append(model)
        return self.definitions

    def generate_swagger(self, dir=''):
        """ One-function-to-call needed function to generate a swagger documentation 
        
            Args:
                dir (str, optional):
                    directory to create the yaml file
        """
        for i in self.collections:
            col = i()
            self.get_operations(col)
            self.get_model_definitions(col)
        return self.write_to_yaml(dir)
