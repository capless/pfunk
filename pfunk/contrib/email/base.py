import warnings

from envs import env
from valley.utils import import_util

from pfunk.contrib.templates import temp_env


class EmailBackend(object):
    """
    Base email backend class
    """
    def get_template(self, template:str):
        """
        Get the template based on the template location string
        Args:
            template: template location string

        Returns: str

        """
        return temp_env.get_template(template)

    def send_email(self):
        raise NotImplementedError

    def get_body_kwargs(self, html_template=None, txt_template=None, **kwargs):
        """
        Builds the HTML and text email templates based on the supplied keyword arguments.
        Args:
            html_template: HTML template location string
            txt_template: Text template location string
            **kwargs: keyword arguments used to render the template(s)

        Returns: dict

        """
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
    """
    Sends email
    Args:
        subject: Email subject
        to_emails: List of email addresses
        html_template: HTML template location string
        txt_template: Text template location string
        from_email: From email address
        cc_emails: Email addresses to CC
        bcc_emails: Email address to BCC
        fail_silently: Specifies whether to fail silently
        backend: Specifies what backend to use. (default: pfunk.contrib.email.ses.SESBackend)
        **kwargs: keyword arguments to render template(s)

    Returns: None

    """
    email_backend = import_util(backend or env('EMAIL_BACKEND', 'pfunk.contrib.email.ses.SESBackend'))

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=ResourceWarning)
        email_backend().send_email(subject=subject, to_emails=to_emails, html_template=html_template,
                              txt_template=txt_template, from_email=from_email, cc_emails=cc_emails,
                              bcc_emails=bcc_emails, fail_silently=fail_silently, **kwargs)