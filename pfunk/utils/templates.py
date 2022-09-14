from envs import env
from jinja2 import Environment
from jinja2.loaders import ChoiceLoader, PackageLoader, FileSystemLoader


def get_loaders():
    """
    Get the Jinja2 loaders for the project.
    Returns: list
    """
    loaders = [
        FileSystemLoader(env('TEMPLATE_ROOT_DIR')),
        PackageLoader('pfunk.contrib.auth'),
        PackageLoader('pfunk.contrib.ecommerce'),
    ]
    for i in env('TEMPLATE_PACKAGES', [], var_type='list'):
        loaders.append(PackageLoader(i))
    return loaders


temp_env = Environment(loader=ChoiceLoader(get_loaders()))
