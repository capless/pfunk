import collections
import json
import requests
import stripe
import bleach
from envs import env
from datetime import datetime
from json import JSONDecodeError
from jinja2 import Environment, BaseLoader

from ecommerce.models import Customer, Package
from pfunk.contrib.email import ses
from pfunk.exceptions import DocNotFound
from pfunk.web.views.json import JSONView, ListView, DetailView
from pfunk.contrib.email.ses import SESBackend
from pfunk.contrib.auth.collections import Group, User

stripe.api_key = env('STRIPE_API_KEY')
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
DOMAIN_NAME = env('DOMAIN_NAME')

class PackageListView(ListView):
    model = Package
    login_required = True


package_list_view = PackageListView.as_view()


class CheckoutView(DetailView):
    model = Package
    login_required = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = Customer.objects.get_or_create_customer(self.request.user)
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer=customer.customer_id,
            billing_address_collection='required',
            client_reference_id=self.object.stripe_id,
            metadata={
                'user_id': self.request.user.id
            },
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product': self.object.stripe_id,
                    'unit_amount': self.object.stripe_price,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=self.get_success_url(),
            cancel_url=self.get_cancel_url(),
        )

        context['CHECKOUT_SESSION_ID'] = session.id
        context['STRIPE_PUB_KEY'] = STRIPE_PUBLISHABLE_KEY
        return context


checkout_view = CheckoutView.as_view()


class CheckoutSuccessView(DetailView):
    model = Package
    login_required = True

    def get_object(self, queryset=None):
        try:
            session_id = self.request.GET['session_id']
        except KeyError:
            raise DocNotFound
        self.stripe_session = stripe.checkout.Session.retrieve(session_id)
        return self.model.objects.get(stripe_id=self.stripe_session.client_reference_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stripe_session'] = self.stripe_session
        return context


success_url = CheckoutSuccessView.as_view()


class BaseWebhookView(JSONView):
    http_method_names = ['post']
    webhook_signing_secret = STRIPE_WEBHOOK_SECRET

    def event_action(self):

        event_type = self.event.type.replace('.', '_')
        action = getattr(self, event_type, None)
        if isinstance(action, collections.Callable):
            action()
            return {'success': 'ok'}
        raise super().not_found_class()

    def post(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        self.event = self.check_signing_secret()
        self.event_json = json.loads(self.request.body)

        try:
            self.object = self.event.data.object
        except AttributeError:
            self.object = None

        return self.event_action()

    def check_ip(self):
        """
        Makes sure the request is coming from a known Stripe address.
        :return: bool
        """
        try:
            valid_ips = requests.get('https://stripe.com/files/ips/ips_webhooks.json').json()['WEBHOOKS']
        except (KeyError, JSONDecodeError):
            return True
        try:
            return self.request.META['REMOTE_ADDR'] in valid_ips
        except KeyError:
            return False

    def send_html_email(self, subject, from_email: str, to_email_list: list, template_name=None, context=None):
        if not context:
            context = {'object': self.object, 'request_body': self.request.body}
        if template_name:
            rtemplate = Environment(loader=BaseLoader()).from_string(template_name)
            html_content = rtemplate.render(context or dict())
            text_content = bleach.clean(html_content, strip=True)
        else:
            text_content = "{}".format(self.request.body)
            html_content = "{}".format(self.request.body)

        msg = SESBackend()
        msg.send_email(
            subject=subject,
            to_emails=to_email_list,
            html_template=template_name,
            txt_template=text_content,
            from_email=from_email,
        )

    def check_signing_secret(self):
        """
        Make sure the request's Stripe signature to make sure it matches our signing secret.
        :return: HttpResponse or Stripe Event Object
        """
        # If we are running tests we can't verify the signature but we need the event objects

        event = stripe.Webhook.construct_event(
            self.request.body, self.request.META['HTTP_STRIPE_SIGNATURE'], self.webhook_signing_secret
        )
        return event

    def get_transfer_data(self):
        return self.event_json['data']['object']


class WebHookView(BaseWebhookView):
    
    def __init__(self, group=Group, user=User):
        self.User = user
        self.Group = group

    def checkout_session_completed(self):
        # TODO: Determine what should be the strucutre of this function
        # If User > Group or Group > User, the current structure is Group > User
        u = self.User.get(ref=self.object.metadata.user_id)
        p = Package.get(stripe_id=self.object.client_reference_id)  # TODO: see if query like this is possible

        try:
            group = self.Group.get(
                title=f'{p.title} Group ({datetime.now()})', package=p
            )
        except DocNotFound:
            group = self.Group.create(
                title=f'{p.title} Group ({datetime.now()})', package=p
            )
    
        self.send_html_email('New Project', DEFAULT_FROM_EMAIL, [u.email],
                            'ecommerce/emails/new-project.html', {'group': group,
                                                                'domain_name': DOMAIN_NAME})

webhook_view = WebHookView.as_view()