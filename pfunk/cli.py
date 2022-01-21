import click
import json
import os
import sys
import datetime

from jinja2 import TemplateNotFound
from valley.utils import import_util
from werkzeug.serving import run_simple
from pfunk.client import FaunaClient, q

from pfunk.contrib.auth.collections import Group, PermissionGroup
from pfunk.exceptions import DocNotFound
from pfunk.template import wsgi_template, project_template, collections_templates, key_template
from pfunk.utils.deploy import Deploy


@click.group()
def pfunk():
    pass


def load_config_file(filename):
    with open(filename, 'r') as f:
        config = json.load(f)
    return config

@pfunk.command()
@click.option('--generate_local_key', prompt=True, help='Specifies whether to generate a local database and key',
              default=False)
@click.option('--stage_name', prompt=True, help='Application stage', default='dev')
@click.option('--email', prompt=True, help='Default From Email')
@click.option('--bucket', prompt=True, help='S3 Bucket')
@click.option('--fauna_key', prompt=True, help='Fauna Key')
@click.option('--api_type', type=click.Choice(['web', 'rest', 'none']), prompt=True, help='API Type (web, rest, none)')
@click.argument('name')
def init(name: str, api_type: str, fauna_key: str, bucket: str, email: str, stage_name: str, generate_local_key: bool):
    """
    Creates a PFunk project
    Args:
        name: Project name
        api_type: API Gateway type (web, rest, none)
        fauna_key: Fauna secret key
        bucket: S3 Bucket
        email: Default from Email
        stage_name: Application stage

    Returns:

    """
    if not os.path.exists(f'pfunk.json'):
        if not os.path.exists(name):
            os.mkdir(name)
        with open(f'pfunk.json', 'x') as f:
            json.dump({
                'name': name,
                'api_type': api_type,
                'stages': {stage_name: {
                    'key_module': f'{name}.{stage_name}_keys.KEYS',
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
        if generate_local_key:
            client = FaunaClient(secret='secret')
            db_name = f'{name}-local'
            client.query(
                q.create_database({'name': db_name})
            )
            key = client.query(
                q.create_key({'database': q.database(db_name), 'role': 'admin'})
            )
            click.secho(f'Fauna Local Secret (copy into your .env or pipenv file): {key}', fg='green')

    else:
        click.echo('There is already a project file in this directory.')


@pfunk.command()
@click.option('--filename', default='pfunk.json', help='Fauna Key')
@click.option('--fauna_key', prompt=True, help='Fauna Key')
@click.argument('stage_name')
def add_stage(stage_name: str, fauna_key: str, filename: str):
    """
    Adds stage to the project
    Args:
        stage_name: Stage name
        fauna_key: Fauna secret key
        filename: Configuration file name (default: pfunk.json)

    Returns:

    """
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
    """
    Run local WSGI based server to test the web service.
    Args:
        hostname: Hostname to use (default: localhost)
        port: Post that will be used
        wsgi: WSGI module (dot notated path to module)
        config_file: PFunk config file (default: pfunk.json)
        use_debugger: Specifies if the server should show debugging info. (default: True)
        use_reloader: Specifies if the server should auto reload on error (default: True)

    Returns:

    """
    config = load_config_file(config_file)
    sys.path.insert(0, os.getcwd())
    wsgi_path = wsgi or f'{config.get("name")}.wsgi.app'
    app = import_util(wsgi_path)
    run_simple(hostname, port, app, use_debugger=use_debugger, use_reloader=use_reloader)


@pfunk.command()
@click.option('--publish_locally', prompt=True, help='Specifies whether to publish the schema locally.', default=False)
@click.option('--config_path', help='Configuration file path', default='pfunk.json')
@click.option('--project_path', help='Project module path')
@click.argument('stage_name')
def publish(stage_name: str, project_path: str, config_path: str, publish_locally: bool):
    """
    Publish GraphQL schema to Fauna
    Args:
        stage_name: Stage to publish to
        project_path: Project module path
        config_path: Path to the project config file. (default: pfunk.json)

    Returns:

    """
    config = load_config_file(config_path)
    sys.path.insert(0, os.getcwd())
    if not project_path:
        project_path = f'{config.get("name")}.project.project'
    project = import_util(project_path)
    if not publish_locally:

        secret = config['stages'][stage_name]['fauna_secret']
        os.environ['FAUNA_SECRET'] = secret
    project.publish()


@pfunk.command()
@click.option('--config_path', help='Configuration file path', default='pfunk.json')
@click.argument('stage_name')
def seed_keys(stage_name: str, config_path: str):
    """
    Seed encryption keys
    Args:
        stage_name: Stage that the keys should be associated with
        config_path: Configuration path

    Returns:

    """
    config = load_config_file(config_path)
    Key = import_util('pfunk.contrib.auth.collections.Key')
    keys = Key.create_keys()
    name = config.get('name')
    keys_path = f'{name}/{stage_name}_keys.py'
    with open(keys_path, 'w+') as f:
        f.write(key_template.render(keys=keys))
    return keys_path

@pfunk.command()
@click.option('--local_user', help='Specifies whether the user is local.', prompt=True, default=False)
@click.option('--config_path', help='Configuration file path', default='pfunk.json')
@click.option('--project_path', help='Project module path')
@click.option('--username', prompt=True, help='Username')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password')
@click.option('--email', prompt=True, help='Email')
@click.option('--first_name', prompt=True, help='First Name')
@click.option('--last_name', prompt=True, help='Last Name')
@click.option('--group_slug', prompt=True, help='User Group Slug', default=None)
@click.argument('stage_name')
def create_admin_user(stage_name: str, group_slug: str, last_name: str, first_name: str, email: str, password: str, username: str,
                      project_path: str, config_path: str, local_user: bool):
    """
    Create an admin user in the project's Fauna user collection.
    Args:
        stage_name: Stage name
        group_slug: slug of the group that the user should be assigned to
        last_name: Last name of user
        first_name: First name of user
        email: Email address of user
        password: Password for the user
        username: Username for the user
        project_path: Project path
        config_path: Config path
        local_user: Specifies whether to create the user locally.

    Returns:

    """
    config = load_config_file(config_path)
    secret = config['stages'][stage_name]['fauna_secret']
    User = import_util('pfunk.contrib.auth.collections.User')
    if not local_user:
        os.environ['FAUNA_SECRET'] = secret

    user = User.create(
        username=username,
        _credentials=password,
        first_name=first_name,
        last_name=last_name,
        email=email,
        account_status='ACTIVE'
    )

    if group_slug:
        try:
            group = Group.get_by('unique_Group_slug', group_slug)
        except DocNotFound:
            group = Group.create(name=group_slug, slug=group_slug)
        if not project_path:
            project_path = f'{config.get("name")}.project.project'
        sys.path.insert(0, os.getcwd())
        project = import_util(project_path)
        perm_list = []
        for i in project.collections:
            perm_list.append(PermissionGroup(collection=i, permissions=['create', 'write', 'read', 'delete']))
        user.add_permissions(group, perm_list)

@pfunk.command()
@click.option('--config_path', help='Configuration file path')
@click.argument('stage_name')
def deploy(stage_name: str, config_path: str):
    """
    Publish the GraphQL schema and API to Lambda and API Gateway (if applicable)
    Args:
        stage_name: Stage name
        config_path: Config path

    Returns:

    """
    try:
        d = Deploy(config_path=config_path)
    except FileNotFoundError:
        cp = config_path or 'pfunk.json'
        print(f'Deploy Failed: Config path ({cp}) not found ')
        return
    d.deploy(stage_name)

if __name__ == '__main__':
    pfunk()

