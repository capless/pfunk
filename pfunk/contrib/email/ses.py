import boto3
from envs import env
from pfunk.contrib.email.base import EmailBackend


class SESBackend(EmailBackend):
    region_name = env('SES_REGION_NAME','us-east-1')

    def send_email(self, template:str, to_emails:list, from_email:str =None, bcc_emails:list = None):
        client = boto3.client("ses", region_name=self.region_name)
        CHARSET = "UTF-8"
        html_template = self.get_template(template)
        html_template.render()

        response = client.send_email(
            Source='string',
            Destination={
                'ToAddresses': [
                    'string',
                ],
                'CcAddresses': [
                    'string',
                ],
                'BccAddresses': [
                    'string',
                ]
            },
            Message={
                'Subject': {
                    'Data': 'string',
                    'Charset': 'string'
                },
                'Body': {
                    'Text': {
                        'Data': 'string',
                        'Charset': 'string'
                    },
                    'Html': {
                        'Data': 'string',
                        'Charset': 'string'
                    }
                }
            },
            ReplyToAddresses=[
                'string',
            ],
            ReturnPath='string',
            SourceArn='string',
            ReturnPathArn='string',
            Tags=[
                {
                    'Name': 'string',
                    'Value': 'string'
                },
            ],
            ConfigurationSetName='string'
        )
        #
        # response = ses_client.send_email(
        #     Destination={
        #         "ToAddresses": [
        #             "abhishek@learnaws.org",
        #         ],
        #     },
        #     Message={
        #         "Body": {
        #             "Html": {
        #                 "Charset": CHARSET,
        #                 "Data": HTML_EMAIL_CONTENT,
        #             }
        #         },
        #         "Subject": {
        #             "Charset": CHARSET,
        #             "Data": "Amazing Email Tutorial",
        #         },
        #     },
        #     Source="abhishek@learnaws.org",
        # )