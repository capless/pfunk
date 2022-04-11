import boto3
import swaggyp as sw
# from botocore.exceptions import BadReq
from envs import env
from openapi_spec_validator import validate_v2_spec, openapi_v2_spec_validator
from openapi_spec_validator.readers import read_from_filename
from openapi_spec_validator.exceptions import OpenAPIValidationError


class ApiGateway(object):
    region_name = env('SES_REGION_NAME', 'us-east-1')

    def __init__(self):
        self.client = boto3.client('apigateway', region_name=self.region_name)

    def validate_yaml(self, yaml_file):
        """ Validate YAML file if it is valid for using OpenAPI Spec v2"""
        try:
            spec_dict, spec_url = read_from_filename(yaml_file)
            validate_v2_spec(spec_dict)
        except (OSError, AttributeError) as err:
            return {'errors': str(err)}
        except OpenAPIValidationError as err:
            return self._iterate_validator_errors(spec_dict)
        return None

    def _iterate_validator_errors(self, spec_dict):
        """ Iterates through list of errors that the `openapi_spec_validator` returned 
        
            This method was implemented due to `openapi_spec_validator` design
            that if an error happened while iterating through the YAML file
            it returns a Python error.

            Args:
                spec_dict (dict, required):
                    `spec_dict` generated from `openapi_spec_validator.readers.read_from_filename`
            Returns:
                list of errors
        """
        try:
            errors = [{err.message: err.json_path}
                      for err in openapi_v2_spec_validator.iter_errors(spec_dict)]
            return errors
        except (OSError, AttributeError) as err:
            return str(err)

    def create_api_from_yaml(self, yaml_file, fail_on_warnings=True):
        """ Creates an API for AWS API Gateway from a YAML swagger file 
        
        Args:
            yaml_file (yaml file, required):
                The OpenAPI swagger file to create API from
            fail_on_warnings (bool, optional):
                Specifies if the method will error on warnings. Default: `True` 
        """
        _yaml_valid = self.validate_yaml(yaml_file)
        if _yaml_valid:
            return {
                "error": 'Bad Request. YAML is not valid.',
                "yaml_err": _yaml_valid
            }

        try:
            if not type(yaml_file) == 'string':
                with open(yaml_file, 'r') as file:
                    response = self.client.import_rest_api(
                        failOnWarnings=fail_on_warnings,
                        body=file
                    )
            else:
                response = self.client.import_rest_api(
                    failOnWarnings=fail_on_warnings,
                    body=yaml_file
                )

            if response:
                return {
                    'success': True,
                    response: response
                }
        # TODO: Specify boto exceptions
        except Exception as err:
            return err

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
