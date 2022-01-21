import boto3
import datetime
import json
import os
import pip
import shutil
import sammy as sm

s3 = boto3.client('s3')


class Deploy(object):
    """ Deploys the API to S3 and CloudFormation
    
    Args:
        config_path (str, required):
            path of the project

    Attributes:
        config_path (str, required): 
            path of the project

    """
    config_path = 'pfunk.json'
    build_folder = '_build'
    requirements_file_name = 'requirements.txt'
    python_version = 'python3.9'

    def __init__(self, config_path=None):
        self.config_path = config_path or self.config_path
        self.project_folder = f'{os.path.dirname(os.path.abspath(self.config_path))}'
        self.build_path = f'{self.project_folder}/{self.build_folder}'
        self.requirements_file_path = f'{self.project_folder}/{self.requirements_file_name}'
        self.config = self.load_config()
        self.project_name = self.config.get('name')

    def load_config(self):
        config = None
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        return config

    def deploy(self, stage_name):
        """ Zips the package, install, uploads to s3 and publishes to CloudFormation """
        try:
            stage_settings = self.config.get('stages')[stage_name]
        except KeyError:
            print(f'The "{stage_name}" stage does not exist.')
            return
        try:
            bucket = stage_settings['bucket']
        except KeyError:
            print(f'Bucket for {stage_name} stage not specified.')
            return

        zip_name = self.get_zip_name(stage_name)
        self.copy_app_files()
        self.install_packages()
        zip_file = self.build_zip(zip_name)
        self.upload_zip(zip_file, bucket)
        try:
            self.build_template(stage_name, bucket, zip_file, stage_settings)
        except Exception as e:
            print(f'Build Failed: {e}')

        self.remove_build_artifacts(stage_name, zip_name)

    def copy_app_files(self):

        shutil.copytree(f'{self.project_folder}/{self.project_name}', f'{self.build_path}/{self.project_name}',
                        ignore=shutil.ignore_patterns(
                            self.config_path, self.requirements_file_path))

    def install_packages(self):
        print(f'Installing packages from {self.requirements_file_path}')
        pip.main(['install', '-r',
                  self.requirements_file_path,
                  '-t', self.build_path])

    def get_zip_name(self, stage_name):
        timestamp = datetime.datetime.now().timestamp()
        return f'{self.project_name}-{stage_name}-{timestamp}'

    def build_zip(self, zip_name):
        print(f'Zipping: {zip_name}')
        shutil.make_archive(zip_name, 'zip', self.build_path)
        return f'{zip_name}.zip'

    def upload_zip(self, zip_file, bucket):
        print(f'Uploading Zip {zip_file} to {bucket} bucket.')
        s3.upload_file(zip_file, bucket, zip_file)

    def remove_build_artifacts(self, stage_name, zip_name):
        """ Cleans up the uneeded files that was created
            prior to deploy (successful or not)
        """
        zip_file = f'{zip_name}.zip'
        print('Removing build path')
        shutil.rmtree(self.build_path)
        print(f'Removing {zip_file}')
        os.remove(f'{zip_file}')

    def get_env_vars(self, stage_name, stage_settings):
        return {
            'STAGE_NAME': stage_name,
            'FAUNA_SECRET': stage_settings.get('fauna_secret'),
            'DEFAULT_FROM_EMAIL': stage_settings.get('default_from_email'),
            'TEMPLATE_ROOT_DIR': f'/var/task/{self.project_name}/templates',
            'KEY_MODULE': stage_settings.get('key_module')
        }

    def build_template(self, stage_name, bucket, zip_name, stage_settings):
        """ Generates AWS SAM yaml template and publishes it to CloudFormation """
        sam = sm.SAM(Description=self.config.get('description'), render_type='yaml')

        sam.add_parameter(sm.Parameter(name='Bucket', Type='String'))

        sam.add_parameter(sm.Parameter(name='CodeZipKey', Type='String'))

        logical_id = f'{self.project_name}{stage_name.capitalize()}'
        sam.add_resource(sm.Function(
            name=logical_id,
            CodeUri=sm.S3URI(
                Bucket=sm.Ref(Ref='Bucket'), Key=sm.Ref(Ref='CodeZipKey')),
            Handler=f'{self.project_name}.project.handler',
            Runtime=self.python_version,
            Environment=sm.Environment(Variables=self.get_env_vars(stage_name, stage_settings)),
            Events=[sm.APIEvent(name=logical_id, Path='{proxy+}', Method='any')]
        ))

        sam.publish(logical_id, Bucket=bucket, CodeZipKey=zip_name)
