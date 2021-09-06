from jinja2.loaders import FileSystemLoader, Environment


class EmailBackend(object):

    def get_template(self, template:str):
        temp_env = Environment(
            loader=FileSystemLoader('templates')
        )
        return temp_env.get_template(template)

    def send_email(self):
        raise NotImplementedError