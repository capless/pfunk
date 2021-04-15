# PFunk
A Python library to make writing applications with FaunaDB easier. Includes GraphQL and generic ABAC auth workflow integrations.

## Table of Contents

- [Getting Started](#Getting-Started)
    - [Installation](#Installation)
    - [Setup the Connection](#setup-the-connection)
        - [Environment Variables Method](#using-environment-variables-preferred-method)
        - [Hard Coding Key](#hard-coding-client)
    - [Define your Collections](#define-your-collections-collectionspy)
    - [Choose an Auth Workflow](#choose-an-auth-workflow)
    - [Publish](#publish)
    - [Save Some Data](#save-some-data)
    - [Query Your Data](#query-your-data)
    - [Delete a Record](#delete-a-record)
- [API Reference](#api-reference)
    - [Collections](#collections)
    - [Resources](#resources)
        - [Functions](#functions)
        - [Indexes](#indexes)
        - [Roles](#-roles)
    - [Contrib](#contrib)
        - [Auth](#auth)
            - [User Collection](#user-collection-pfunkcontribauthcollectionsuser)
            - [Group Collection](#group-collection-pfunkcontribauthcollectionsgroup)
            - [Auth Functions](#auth-functions)
            - [Auth Roles](#auth-roles)
        


### Getting Started {#Getting-Started}

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
### Choose an Auth Workflow

Currently, you can choose a **group based** workflow, **user based**, or a **mix** of the two.  

### Publish

### Save Some Data

### Query your Data

### Delete a Record

## API Reference

### Collections

### Fields

### DB

### Client

### Resources

#### Functions

#### Indexes 

#### Roles

### Contrib

#### Auth

##### Collections

##### User Collection (pfunk.contrib.auth.collections.User)

##### Group Collection (pfunk.contrib.auth.collections.Group)

##### Auth Functions

##### Auth Roles
