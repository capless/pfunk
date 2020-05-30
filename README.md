# PFunk

A Python library created make building [FaunaDB](https://fauna.com) GraphQL schemas and authentication code easier.

## Getting Started

```python
from pfunk import Collection, Enum, Index, StringField, IntegerField
from pfunk.db import Database, Index, TermValue, TermValueField, Binding


make_term_field = TermValueField(name='make')
make_term = TermValue(fields=[make_term_field])
make_index = Index(name='make-index', source='Car', terms=make_term)

cars_index = Index(name='cars', source='Car')


class Car(Collection):
    make = StringField(required=True)
    model = StringField(required=True)
    year = IntegerField(required=True)
    transmission = StringField(required=True)
    title_status = StringField(required=True)
    vin = StringField(required=True)
    color = StringField()

d = Database(name='capless-dev')
# Create the database on Fauna
d.create()
# Add Car collection to the database so it will be created when we publish 
d.add_resource(Car)
# Publish GraphQL and Indexes
d.publish()

```