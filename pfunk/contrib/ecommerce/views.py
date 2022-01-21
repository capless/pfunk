import collections
import json
import requests
import stripe
import bleach
from envs import env
from datetime import datetime
from json import JSONDecodeError
from jinja2 import Environment, BaseLoader

from pfunk.contrib.email import ses
from pfunk.exceptions import DocNotFound
from pfunk.web.views.json import JSONView, ListView, DetailView, CreateView
from pfunk.contrib.email.ses import SESBackend
from pfunk.contrib.auth.collections import Group, User
from pfunk.web.views.base import ActionMixin

stripe.api_key = env('STRIPE_API_KEY')
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
DOMAIN_NAME = env('DOMAIN_NAME')


class ListStripePackage(ListView):
    """ Listing of available packages should be public """
    login_required = False


class DetailStripePackage(DetailView):
    """ Detail of available packages should be public """
    login_required = False


class CheckoutView(DetailView):
    """ Returns a Stripe Checkout View session

        This is a session from Stripe itself, using this
        is a better way of handling payments and showing
        the different of options of payment. Use this as
        a base class.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.collection.objects.get_or_create_customer(
            self.request.user)   # `StripeCustomer` collection
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


class CheckoutSuccessView(DetailView):
    """ Defines action from the result of `CheckoutView` """

    def get_object(self, queryset=None):
        """ Acquires the object from the `SessionView` """
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


class BaseWebhookView(JSONView, ActionMixin):
    """ Base class to use for executing Stripe webhook actions """
    action = 'webhook'
    http_method_names = ['post']
    webhook_signing_secret = STRIPE_WEBHOOK_SECRET

    def event_action(self):
        """ Transforms Stripe action to snake case for easier 
            calling in child class

            For example, the event type `checkout.session.completed`
            will transform to `checkout_session_completed` which 
            you can use in your child class as the function name
            to execute the action you want if the event type was
            that
        """
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
            valid_ips = requests.get(
                'https://stripe.com/files/ips/ips_webhooks.json').json()['WEBHOOKS']
        except (KeyError, JSONDecodeError):
            return True
        try:
            return self.request.META['REMOTE_ADDR'] in valid_ips
        except KeyError:
            return False

    def send_html_email(self, subject, from_email: str, to_email_list: list, template_name=None, context=None):
        """ Sends an HTML email 

            Uses `contrib.email` service which uses `boto3`
            You can define these 2 in your environment variables:
                SES_REGION_NAME (str, default: `us-east-1`): region name of AWS service
                DEFAULT_FROM_EMAIL (str): default `from` email
        """
        if not context:
            context = {'object': self.object,
                       'request_body': self.request.body}
        if template_name:
            rtemplate = Environment(
                loader=BaseLoader()).from_string(template_name)
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

    def checkout_session_completed(self):
        """ A method to override to implement custom actions 
            after successful Stripe checkout

            Use this method by subclassing this class in your
            custom claas
        """
        raise NotImplementedError
