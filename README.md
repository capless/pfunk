# PFunk
A Python library to make writing applications with FaunaDB easier. Includes GraphQL and generic ABAC auth workflow integrations.

## Table of Contents

- [Getting Started](#Getting-Started)
    - [Installation](#Installation)
    - [Setup the Connection](#setup-the-connection)
        - [Environment Variables Method](#using-environment-variables-preferred-method)
        - [Hard Coding Key](#hard-coding-client)
    - [Define your Collections](#define-your-collections-collectionspy)
    - [Choose an Auth Workflow](#auth-workflows)
    - [Publish](#publish)
    - [Save Some Data](#save-some-data)
    - [Query Your Data](#query-your-data)
    - [Delete a Record](#delete-a-record)
- [API Reference](#api-reference)
    - [Collections](#collections)
      - [Hard Coded Client]()
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

### Define your Collections (collections.py) 
```python
from pfunk.db import Database
from pfunk import Collection, EnumField, StringField, Enum, ReferenceField, ManyToManyField
from pfunk.contrib.auth.collections import User, Group # Base user and group collections for authentication
from pfunk.contrib.auth.resources import GenericGroupBasedRole, GenericUserBasedRole

db = Database(name='demo')


class Category(Collection):
    _roles = [GenericUserBasedRole]
    name = StringField(required=True)
    user = ReferenceField(User)
    
    def __unicode__(self):
        return self.name
    
    
class Video(Collection):
    _roles = [GenericGroupBasedRole, GenericUserBasedRole]
    name = StringField(required=True)
    url = StringField(required=True)
    user = ReferenceField(User, required=True)
    group = ReferenceField(Group, required=False)

    def __unicode__(self):
        return self.name

    
db.add_resource(Video)
```
### Auth Workflows

In the example above, the ```_roles``` list on the ```Collection``` classes attaches generic roles to the 
collection.  Currently, you can choose a **group based** workflow, **user based**, or a **mix** of the two.

### Publish

```python
db.publish()
```

### Create Group and User
The code below will create a new user, group, and users_groups (many-to-many relationship through collection) record.
```python
from pfunk.contrib.auth.collections import Group, User
group = Group.create(name='base', slug='base')
user = User.create_user(username='goat23', first_name='Michael', last_name='Jordan', email='goat@example.com',  
                        account_status='ACTIVE', password='cruelpass', groups=[group])
```

### Login

```python
from pfunk.contrib.auth.collections import User

#The login classmethod returns the authenticated token if the credentials are correct.
token = User.login('goat23', 'cruelpass')
```
### Save Some Data
Let's use the Video collection, and the authenticated token we created above to save some data.

```python
# Use the token from above so the current users permissions are used.
User._token = token
Video._token = token


video = Video.create(
    name='Demo Video',
    url='https://somevideosite.com/v/aasfsdfdsaffddsf',
    user=User.get_from_id() # Get the currently logged in user
) 

```

### Query your Data
Let's get the video you just created.

```python
video = Video.get('the-key-for-the-previous-video')
```

Let's query for all videos using the server key.

```python
videos = Video.all()
```

Let's query for all videos that the logged in user has access to.

```python
Video._token = token # Use the token we created earlier

videos = Video.all()
```

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

###### Hard Coding Collections

**IMPORTANT:** This is not the recommended method for connecting pFunk to Fauna with **server** or **admin** keys. 
We recommend using an environment variable named ```FAUNA_SECRET```.
Please keep in mind this recommendation does not include using authenticating with keys acquired from the **login** 
function.  
```python
from pfunk.client import FaunaClient

client = FaunaClient(secret='your-secret-key')
```
In your **collections.py** import the **client** from the previous step.
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

##### User Collection (pfunk.contrib.auth.collections.User)

##### Group Collection (pfunk.contrib.auth.collections.Group)

##### Auth Functions

##### Auth Roles
