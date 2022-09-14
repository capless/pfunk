import stripe
from envs import env
from valley.utils import import_util

from pfunk.collection import Collection
from pfunk.contrib.auth.resources import GenericGroupBasedRole, GenericUserBasedRole
from pfunk.contrib.ecommerce.views import ListStripePackage, DetailStripePackage, CheckoutSuccessView, BaseWebhookView
from pfunk.exceptions import DocNotFound
from pfunk.fields import ReferenceField, StringField, FloatField
from pfunk.web.views.json import CreateView, UpdateView, DeleteView

stripe.api_key = env('STRIPE_API_KEY')


User = import_util(env('USER_COLLECTION', 'pfunk.contrib.auth.collections.User'))
Group = import_util(env('GROUP_COLLECTION', 'pfunk.contrib.auth.collections.Group'))


class StripePackage(Collection):
    """ Collection that has the essential info about a stripe package 
    
        This is only a base model made to give an idea how 
        can you structure your collections. Override the 
        fields and functions to match your system.

        Read and detail views are naturally public. Write operations
        requires authentication from admin group. While it grealty
        depends on your app, it is recommended to have this only
        modified by the admins and use `StripeCustomer` model to
        attach a `stripe_id` to a model that is bound for payment.
    """
    use_crud_views = False
    collection_roles = [GenericGroupBasedRole]
    collection_views = [ListStripePackage, DetailStripePackage,
                        CheckoutSuccessView, CreateView, UpdateView, DeleteView]
    stripe_id = StringField(required=True)
    name = StringField(required=True)
    price = FloatField(required=True)
    description = StringField(required=True)
    group = ReferenceField(Group)

    def __unicode__(self):
        return self.name

    @property
    def stripe_price(self):
        return int(self.price * 100)


class StripeCustomer(Collection):
    """ Base Customer collection for Stripe 

        This is only a base model made to give an idea how 
        can you structure your collections. Override the 
        fields and functions to match your system.
    """
    collection_roles = [GenericUserBasedRole]
    collection_views = [BaseWebhookView]
    user = ReferenceField(User)
    stripe_id = StringField(required=True, unique=True)

    def __unicode__(self):
        return self.customer_id

    def get_or_create_customer(self, user):
        """ Acquires the Stripe Customer, if not found, create it. 
        
        Returns:
            StripeCustomer (required):
                The instance of this class returned as object
        """
        try:
            return self.get(user=user)
        except DocNotFound:
            sc = stripe.Customer.create(
                description=f"{user.username}",
                email=user.email,
                name=f'{user.first_name} {user.last_name}',
                metadata={'user_id': user.pk, 'username': user.username}
            )
            return self.create(
                user=user, customer_id=sc.id
            )
