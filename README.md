# PFunk

A Python library created make building [FaunaDB](https://fauna.com) GraphQL schemas and authentication code easier.

## Getting Started

```python
from pfunk import Collection, StringField, IntegerField
from pfunk.db import Database

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

## Authentication

## Indexes

## Functions
