from jinja2.loaders import FileSystemLoader, Environment
from envs import env
from valley.utils import import_util


class EmailBackend(object):

    def get_template(self, template:str):
        temp_env = Environment(
            loader=FileSystemLoader('templates')
        )
        return temp_env.get_template(template)

    def send_email(self):
        raise NotImplementedError

    def get_body_kwargs(self, html_template=None, txt_template=None, **kwargs):
        body_kwargs = {}

        if html_template:
            html_template = self.get_template(html_template)
            html_email = html_template.render(**kwargs)
            body_kwargs['Html'] = {
                'Data': html_email,
                'Charset': self.charset
            }

        if txt_template:
            txt_template = self.get_template(txt_template)
            txt_email = txt_template.render(**kwargs)
            body_kwargs['Text'] = {
                'Data': txt_email,
                'Charset': self.charset
            }

        return body_kwargs


def send_email(subject: str, to_emails: list, html_template: str = None, txt_template: str = None,
               from_email: str = None, cc_emails: list = [], bcc_emails: list = [], fail_silently: bool = True,
               backend=None, **kwargs):
    email_backend = import_util(backend or env('EMAIL_BACKEND', 'pfunk.contrib.email.ses.SESBackend'))

    email_backend().send_email(subject=subject, to_emails=to_emails, html_template=html_template,
                              txt_template=txt_template, from_email=from_email, cc_emails=cc_emails,
                              bcc_emails=bcc_emails, fail_silently=fail_silently, **kwargs)