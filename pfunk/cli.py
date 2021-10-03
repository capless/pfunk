import click
import json
import os
import sys

from jinja2 import TemplateNotFound
from valley.utils import import_util
from werkzeug.serving import run_simple

from pfunk.contrib.auth.collections import Group
from pfunk.template import wsgi_template, project_template, collections_templates
from pfunk.utils.deploy import Deploy


@click.group()
def pfunk():
    pass


def load_config_file(filename):
    with open(filename, 'r') as f:
        config = json.load(f)
    return config

@pfunk.command()
@click.option('--stage_name', prompt=True, help='Application stage', default='dev')
@click.option('--email', prompt=True, help='Default From Email')
@click.option('--bucket', prompt=True, help='S3 Bucket')
@click.option('--fauna_key', prompt=True, help='Fauna Key')
@click.option('--api_type', type=click.Choice(['web', 'rest', 'none']), prompt=True, help='API Type (web, rest, none)')
@click.argument('name')
def init(name: str, api_type: str, fauna_key: str, bucket: str, email: str, stage_name: str):
    if not os.path.exists(f'pfunk.json'):
        if not os.path.exists(name):
            os.mkdir(name)
        with open(f'pfunk.json', 'x') as f:
            json.dump({
                'name': name,
                'api_type': api_type,
                'stages': {stage_name: {
                    'fauna_secret': fauna_key,
                    'bucket': bucket,
                    'default_from_email': email
                }}
            }, f, indent=4, sort_keys=True)
        open(f'{name}/__init__.py', 'x').close()
        with open(f'{name}/wsgi.py', 'x') as f:
            f.write(wsgi_template.render(PFUNK_PROJECT=f'{name}.project.project'))
        with open(f'{name}/project.py', 'x') as f:
            f.write(project_template.render())
        with open(f'{name}/collections.py', 'x') as f:
            f.write(collections_templates.render())
    else:
        click.echo('There is already a project file in this directory.')


@pfunk.command()
@click.option('--filename', default='pfunk.json', help='Fauna Key')
@click.option('--fauna_key', prompt=True, help='Fauna Key')
@click.argument('stage_name')
def add_stage(stage_name: str, fauna_key: str, filename: str):
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            config = json.load(f)
            config['stages'][stage_name] = {'fauna_key': fauna_key}
        with open(filename, 'w+') as f:
            f.write(json.dumps(config))
    else:
        click.echo('You have not run the init command yet.')

@pfunk.command()
@click.option('--use_reloader', default=True)
@click.option('--use_debugger', default=True)
@click.option('--config_file', default='pfunk.json')
@click.option('--wsgi', default=None)
@click.option('--port', default=3434)
@click.option('--hostname', default='localhost')
def local(hostname: str, port: int, wsgi: str, config_file: str, use_debugger: bool, use_reloader: bool):
    config = load_config_file(config_file)
    sys.path.insert(0, os.getcwd())
    wsgi_path = wsgi or f'{config.get("name")}.wsgi.app'
    app = import_util(wsgi_path)
    run_simple(hostname, port, app, use_debugger=use_debugger, use_reloader=use_reloader)


@pfunk.command()
@click.option('--config_path', help='Configuration file path', default='pfunk.json')
@click.option('--project_path', help='Project module path')
@click.argument('stage_name')
def publish(stage_name: str, project_path: str, config_path: str):
    config = load_config_file(config_path)
    sys.path.insert(0, os.getcwd())
    if not project_path:
        project_path = f'{config.get("name")}.project.project'
    project = import_util(project_path)
    secret = config['stages'][stage_name]['fauna_secret']
    os.environ['FAUNA_SECRET'] = secret
    project.publish()


@pfunk.command()
@click.option('--config_path', help='Configuration file path', default='pfunk.json')
@click.argument('stage_name')
def seed_keys(stage_name: str, config_path: str):
    config = load_config_file(config_path)
    secret = config['stages'][stage_name]['fauna_secret']
    Key = import_util('pfunk.contrib.auth.collections.Key')
    os.environ['FAUNA_SECRET'] = secret
    for i in range(10):
        Key.create_key()


@pfunk.command()
@click.option('--config_path', help='Configuration file path', default='pfunk.json')
@click.option('--username', prompt=True, help='Username')
@click.option('--password', prompt=True, help='Password')
@click.option('--email', prompt=True, help='Email')
@click.option('--first_name', prompt=True, help='First Name')
@click.option('--last_name', prompt=True, help='Last Name')
@click.option('--group_slug', prompt=True, help='User Group Slug', default=None)
@click.option('--permission_list', prompt=True, type=click.Tuple([list]), help='Permission List', default=None)
@click.argument('stage_name')
def create_user(stage_name: str, permission_list: tuple, group_slug: str, last_name: str, first_name: str, email: str, password: str, username: str,
                      config_path: str):
    config = load_config_file(config_path)
    secret = config['stages'][stage_name]['fauna_secret']
    User = import_util('pfunk.contrib.auth.collections.User')
    os.environ['FAUNA_SECRET'] = secret
    try:
        user = User.create(
            username=username,
            _credentials=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            account_status='ACTIVE'
        )
    except TemplateNotFound:
        pass
    if group_slug:
        group = Group.get_by('unique_Group_slug', group_slug)
        user.add_permissions(group, permission_list)

@pfunk.command()
@click.option('--config_path', help='Configuration file path')
@click.argument('stage_name')
def deploy(stage_name: str, config_path: str):
    try:
        d = Deploy(config_path=config_path)
    except FileNotFoundError:
        cp = config_path or 'pfunk.json'
        print(f'Deploy Failed: Config path ({cp}) not found ')
        return
    d.deploy(stage_name)

if __name__ == '__main__':
    pfunk()

