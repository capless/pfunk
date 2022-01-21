import boto3
from envs import env
from pfunk.contrib.email.base import EmailBackend


class SESBackend(EmailBackend):
    """
    AWS SES email backend (https://aws.amazon.com/ses/)
    """
    region_name = env('SES_REGION_NAME', 'us-east-1')
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
        # Create Boto3 Client
        client = boto3.client("ses", region_name=self.region_name)

        res = client.send_email(
            Source=from_email or env('DEFAULT_FROM_EMAIL'),
            Destination={
                'ToAddresses': to_emails,
                'CcAddresses': cc_emails,
                'BccAddresses': bcc_emails
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': self.charset
                },
                'Body': self.get_body_kwargs(html_template=html_template, txt_template=txt_template, **kwargs)
            }
        )
        
        return res