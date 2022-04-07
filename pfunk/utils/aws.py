import boto3
import swaggyp as sw
from openapi_spec_validator import validate_v2_spec, openapi_v2_spec_validator
from openapi_spec_validator.readers import read_from_filename
from openapi_spec_validator.exceptions import OpenAPIValidationError


class ApiGateway(object):

    def __init__(self):
        self.client = boto3.client('apigateway')
        pass

    def validate_yaml(self, yaml_file):
        """ Validate YAML file if it is valid for using OpenAPI Spec v2"""
        try:
            spec_dict, spec_url = read_from_filename(yaml_file)
            validate_v2_spec(spec_dict)
        except OpenAPIValidationError as err:
            errors = [{err.message: err.json_path}
                      for err in openapi_v2_spec_validator.iter_errors(spec_dict)]
            return errors
        return None

    def create_api_from_yaml(self, yaml_file):
        # response = client.import_rest_api(
        #     failOnWarnings=True|False,
        #     parameters={
        #         'string': 'string'
        #     },
        #     body=b'bytes'|file
        # )
        pass

    def update_api_from_yaml(self, yaml_file):
        # response = client.put_rest_api(
        #     restApiId='string',
        #     mode='merge'|'overwrite',
        #     failOnWarnings=True|False,
        #     parameters={
        #         'string': 'string'
        #     },
        #     body=b'bytes'|file
        # )
        pass
