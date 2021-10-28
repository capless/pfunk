import stripe
from envs import env

from pfunk.collection import Collection
from pfunk.exceptions import DocNotFound
from pfunk.fields import EmailField, SlugField, ManyToManyField, ListField, ReferenceField, StringField, EnumField, FloatField


stripe.api_key = env('STRIPE_API_KEY')


class StripeCustomer(Collection):
    """ Customer collection for Stripe """
    user = ReferenceField('pfunk.contrib.auth.collections.User')
    customer_id =StringField(required=True)
    
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


class StripePackage(Collection):
    """ Collection that has the essential info about a stripe package """
    stripe_id = StringField(required=True)
    price = FloatField(required=True)
    description = StringField(required=True)

    @property
    def stripe_price(self):
        return int(self.price*100)
