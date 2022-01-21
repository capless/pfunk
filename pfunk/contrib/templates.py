from envs import env
from jinja2 import Environment
from jinja2.loaders import FileSystemLoader


temp_env = Environment(loader=FileSystemLoader(env('TEMPLATE_ROOT_DIR')))