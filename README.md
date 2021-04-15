# PFunk
A Python library to make writing applications with FaunaDB easier. Includes GraphQL and generic ABAC auth workflow integrations.
## Table of Contents

[Getting Started](#Getting Started)

[Auth](#Auth)
### Getting Started

### Installation
```pip install pfunk```

### Setup the Connection

#### Using Environment Variables (Preferred Method)

If you can easily set environment variables just set the ```FAUNA_SECRET``` environment variable to your key.

#### Hard Coding Client
```python
from pfunk.client import FaunaClient

client = FaunaClient(secret='your-secret-key')
```

### Define your Collections (collections.py) 
```python
from pfunk.db import Database
from pfunk import Collection, EnumField, StringField, Enum

# The client from the “Setup the Connection” section
from .client import client

PERSON_ROLE = Enum(name='PersonRole', choices=['teacher', 'student', 'principal'])

db = Database(name='first-database', client=client) #IMPORTANT: This is only necessary if you don't set the ```FAUNA_SECRET``` environment variable.

class Person(Collection):
    _client = client #IMPORTANT: This is only necessary if you don't set the ```FAUNA_SECRET``` environment variable.
    
    name = StringField(required=True)
    email = StringField(required=True)
    role = EnumField(PERSON_ROLE, required=True)

    def __unicode__(self):
        return self.name

    
db.add_resource(Person)
```

### Define your Functions and Roles
```python
from pfunk.resources import Function
from pfunk.client import q

class CreatePerson(Function):
    
    def get_body(self):
        return q.query(
                    q.lambda_(["input"],
                    q.create(
                        q.collection(self.collection.get_collection_name()),
                        

            )
            ))
```

### Define your Indexes (indexes.py)
```python
from pfunk.resources import Index

class AgeIndex(Index):
    name = 'age-index'
    source = 'person'
    terms = []
    values = []
    unique = False
    serialized = True
    
```

## Auth
### Models

#### User Collection (pfunk.contrib.auth.collections.User)

## Indexes

## Functions
