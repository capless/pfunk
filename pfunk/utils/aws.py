import boto3
import swaggyp as sw

class ApiGateway(object):

    def __init__(self):
        self.client = boto3.client('apigateway')
        pass

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
    
    def validate_yaml(self, yaml_file):
        """ Validate YAML file if it is valid for using """
        pass

    def 