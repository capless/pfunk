import datetime
import boto3
import json
import swaggyp as sw
from botocore.exceptions import ClientError, NoCredentialsError
from envs import env
from openapi_spec_validator import validate_v2_spec, openapi_v2_spec_validator
from openapi_spec_validator.readers import read_from_filename
from openapi_spec_validator.exceptions import OpenAPIValidationError

AWS_ACCESS_KEY = env('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = env('AWS_DEFAULT_REGION')


def _json_dt_helper(o):
    """ Helps serializing `datetime` objects to a readable string """
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()


def write_to_config(obj, config_file_dir='pfunk.json'):
    """ Appends object to pfunk config file 
    
    Args:
        obj (dict, required):
            key, value pairs to write to json file
        config_file_dir (str, optional):
            directory of the config json file, default='pfunk.json'
    Returns:
        config_file (dict, required):
            the current value of config file (pfunk.json)
    """
    with open(config_file_dir, 'r+') as f:
        data = json.load(f)
        data.update(obj)
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=4, sort_keys=True, default=_json_dt_helper)
    return data


def read_from_config_file(config_file_dir='pfunk.json'):
    """ Returns data from config file in dict form """
    with open(config_file_dir, 'r') as f:
        data = json.load(f)
    return data


class ApiGateway(object):
    region_name = env('SES_REGION_NAME', 'us-east-1')

    def __init__(self):
        self.client = boto3.client(
            'apigateway',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_DEFAULT_REGION)

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
                    yaml_file = file.read()
            response = self.client.import_rest_api(
                failOnWarnings=fail_on_warnings,
                body=yaml_file)
            if response:
                write_to_config({'api': response})
                return {
                    'success': True,
                    'response': response
                }
        except (ClientError, NoCredentialsError) as err:
            return {
                'error': str(err)
            }

    def update_api_from_yaml(self, yaml_file, mode, rest_api_id=None, fail_on_warnings=True):
        """ Updates rest API using yaml file 
        
        Args:
            rest_api_id (string, required):
                ID of the API for updating, if not provided, use API ID from `pfunk.json`
            yaml_file (yaml file, required):
                The OpenAPI swagger file to create API from
            mode (string, required):
                Mode of update, choice=['merge', 'overwrite']
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
                    yaml_file = file.read()
            # Acquire REST API ID from config file if not provided
            if not rest_api_id:
                data = read_from_config_file()
                if data.get('api'):
                    rest_api_id = (data.get('api')
                                   .get('id'))

            response = self.client.put_rest_api(
                restApiId=rest_api_id,
                mode=mode,
                failOnWarnings=fail_on_warnings,
                body=yaml_file
            )

            if response:
                return {
                    'success': True,
                    'response': response
                }
        except (ClientError, NoCredentialsError) as err:
            return {
                'error': str(err)
            }
