# PFunk
A Python library to make writing applications with FaunaDB easier. Includes GraphQL and generic ABAC auth workflow integrations.
## Github URL
[https://github.com/capless/pfunk](https://github.com/capless/pfunk)
 
## Getting Started

### Installation
```pip install pfunk```

### Setup the Connection

#### Hard Coding Client
```python
from pfunk.client import FaunaClient

client = FaunaClient(secret='your-secret-key')
```
#### Using Environment Variables (Preferred Method)

If you can easily set environment variables just set the ```FAUNA_SECRET``` environment variable to your key.
### Define your Functions and Roles
```python
from pfunk import Function, Role
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
### Define your Collections (collections.py) 
```python
from pfunk import Collection, EnumField, StringField, Enum

# The client from the “Setup the Connection” section
from .client import client

PERSON_ROLE = Enum(name='PersonRole', choices=['teacher', 'student', 'principal'])

class Person(Collection):
    _client = client #IMPORTANT: This is only necessary if you don't set the ```FAUNA_SECRET``` environment variable.
    
    name = StringField(required=True)
    email = StringField(required=True)
    role = EnumField(PERSON_ROLE, required=True)

    def __unicode__(self):
        return self.name
```

### Define your Indexes (indexes.py)
```python
from pfunk import Index
from pfunk.db import 

class AgeIndex(Index):
    name = 'age-index'
    source = 'person'
    terms = []
    values = []
    unique = False
    serialized = True
    
```

## Authentication

## Indexes

## Functions
