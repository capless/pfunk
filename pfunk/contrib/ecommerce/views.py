import collections
import json
from json import JSONDecodeError

import bleach
import requests
import stripe
from envs import env
from jinja2 import Environment, BaseLoader
from werkzeug.routing import Rule

from pfunk.contrib.email.ses import SESBackend
from pfunk.exceptions import DocNotFound
from pfunk.web.views.base import ActionMixin
from pfunk.web.views.json import ListView, DetailView, CreateView

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
            self.request.user)  # `StripeCustomer` collection
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


class CheckoutSuccessView(DetailView, ActionMixin):
    """ Defines action from the result of `CheckoutView` """
    action = 'checkout-success'
    http_method_names = ['get']

    @classmethod
    def url(cls, collection):
        return Rule(f'/{collection.get_class_name()}/{cls.action}/<string:id>/', endpoint=cls.as_view(collection),
                    methods=cls.http_methods)

    def get_query(self, *args, **kwargs):
        """ Acquires the object from the `SessionView` """
        session_id = self.request.kwargs.get('id')
        self.stripe_session = stripe.checkout.Session.retrieve(session_id)
        # NOTE: Chose listing instead of indexing under the assumption of limited  paid packages. Override if needed
        pkg = [pkg for pkg in self.collection.all() if pkg.stripe_id ==
               self.stripe_session.client_reference_id]
        if pkg:
            return pkg
        raise DocNotFound


class BaseWebhookView(CreateView, ActionMixin):
    """ Base class to use for executing Stripe webhook actions """
    login_required = False
    action = 'webhook'
    http_method_names = ['post']
    webhook_signing_secret = STRIPE_WEBHOOK_SECRET

    def get_query(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.event = self.check_signing_secret()
        try:
            self.event_json = json.loads(self.request.body)
        except TypeError:
            self.event_json = self.request.body

        try:
            self.object = self.event.data.object
        except AttributeError:
            self.object = None

        return self.event_action()

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
        if event_type is str:
            action = getattr(self, event_type, None)
            if isinstance(action, collections.Callable):
                action()
                return {'success': 'ok'}
        raise NotImplementedError

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
            return self.request.source_ip in valid_ips
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
            context = {'request_body': self.request.body}
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
        Make sure the request's Stripe signature to make sure it matches our signing secret
        then returns the event

        :return: Stripe Event Object
        """
        # If we are running tests we can't verify the signature but we need the event objects

        event = stripe.Webhook.construct_event(
            self.request.body, self.request.headers['HTTP_STRIPE_SIGNATURE'], self.webhook_signing_secret
        )
        return event

    def get_transfer_data(self):
        return self.event_json['data']['object']

    def checkout_session_completed(self):
        """ A method to override to implement custom actions 
            after successful Stripe checkout.

            This is a Stripe event.
            Use this method by subclassing this class in your
            custom claas
        """
        raise NotImplementedError
