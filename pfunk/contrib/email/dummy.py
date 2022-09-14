from pfunk.contrib.email.base import EmailBackend


class DummyBackend(EmailBackend):
    """
    AWS SES email backend (https://aws.amazon.com/ses/)
    """
    region_name = None
    charset = "UTF-8"

    def send_email(self, subject: str, to_emails: list, html_template: str = None, txt_template: str = None,
                   from_email: str = None, cc_emails: list = [], bcc_emails: list = [], fail_silently: bool = True,
                   **kwargs):
        """
        Sends email
        Args:
            subject: Email subject line
            to_emails: List of email addresses
            html_template: HTML template location string
            txt_template: Text template location string
            from_email: From email address
            cc_emails: CC email addresses
            bcc_emails: BCC email addresses
            fail_silently: Specifies whether to fail silently
            **kwargs: keyword arguments used to render template(s)

        Returns: None

        """
        email_dict = {
            'subject': subject,
            'to_emails': to_emails,
            'html_template': html_template,
            'txt_template': txt_template,
            'from_email': from_email,
            'cc_emails': cc_emails,
            'bcc_emails': bcc_emails,
            'fail_silently': fail_silently,
            'kwargs': kwargs,
            'body': self.get_body_kwargs(html_template=html_template, txt_template=txt_template, **kwargs)
        }
        return email_dict