import click
import json
import os

from valley.utils import import_util
from werkzeug.serving import run_simple
from pfunk.template import wsgi_template, project_template, collections_templates


@click.group()
def pfunk():
    pass


@pfunk.command()
@click.option('--stage', prompt=True, help='Application stage', default='local')
@click.option('--fauna_key', prompt=True, help='Fauna Key')
@click.option('--api_type', type=click.Choice(['web', 'rest', 'none']), prompt=True, help='API Type (web, rest, none)')
@click.argument('name')
def init(name: str, api_type: str, fauna_key: str, stage: str):
    if not os.path.exists(f'{name}/pfunk.json'):
        if not os.path.exists(name):
            os.mkdir(name)
        with open(f'{name}/pfunk.json', 'x') as f:
            json.dump({
                'name': name,
                'api_type': api_type,
                'stages': {stage: {
                    'fauna_key': fauna_key,
                }}
            }, f)
        open(f'{name}/__init__.py', 'x').close()
        with open(f'{name}/wsgi.py', 'x') as f:
            f.write(wsgi_template.render(PFUNK_PROJECT=f'{name}.project'))
        with open(f'{name}/project.py', 'x') as f:
            f.write(project_template.render())
        with open(f'{name}/collections.py', 'x') as f:
            f.write(collections_templates.render())
    else:
        click.echo('There is already a project file in this directory.')


@pfunk.command()
@click.option('--filename', default='pfunk.json', help='Fauna Key')
@click.option('--fauna_key', prompt=True, help='Fauna Key')
@click.argument('stage')
def add_stage(stage: str, fauna_key: str, filename: str):
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            config = json.load(f)
            config['stages'][stage] = {'fauna_key': fauna_key}
        with open(filename, 'w+') as f:
            f.write(json.dumps(config))
    else:
        click.echo('You have not run the init command yet.')

@pfunk.command()
@click.option('--use_reloader', default=True)
@click.option('--use_debugger', default=True)
@click.option('--wsgi', default='wsgi.app')
@click.option('--port', default=3434)
@click.option('--hostname', default='localhost')
def local(hostname: str, port: int, wsgi: str, use_debugger: bool, use_reloader: bool):
    app = import_util(wsgi)
    run_simple(hostname, port, app, use_debugger=use_debugger, use_reloader=use_reloader)

if __name__ == '__main__':
    pfunk()

