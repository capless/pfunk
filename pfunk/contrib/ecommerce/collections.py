import stripe
from envs import env

from pfunk.collection import Collection
from pfunk.contrib.auth.collections.group import Group
from pfunk.contrib.auth.collections.user import User
from pfunk.contrib.auth.resources import GenericGroupBasedRole, GenericUserBasedRole
from pfunk.contrib.ecommerce.views import ListStripePackage, DetailStripePackage
from pfunk.exceptions import DocNotFound
from pfunk.fields import ReferenceField, StringField, FloatField
from pfunk.web.views.json import CreateView, UpdateView, DeleteView

stripe.api_key = env('STRIPE_API_KEY')


class StripePackage(Collection):
    """ Collection that has the essential info about a stripe package 
    
        This is only a base model made to give an idea how 
        can you structure your collections. Override the 
        fields and functions to match your system.

        Read and detail views are naturally public. Write operations
        requires authentication from admin group.
    """
    use_crud_views = False
    collection_roles = [GenericGroupBasedRole]
    collection_views = [ListStripePackage, DetailStripePackage, CreateView, UpdateView, DeleteView]
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
    user = ReferenceField(User)
    customer_id = StringField(required=True)
    package = ReferenceField(StripePackage)

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
