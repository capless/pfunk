# PFunk
A Python library to make writing applications with FaunaDB easier. 
Includes GraphQL and generic ABAC auth workflow integrations.

## Key Features
- DRY (Don't Repeat Yourself) code to help you create multiple collections, indexes, roles, and user-defined functions 
  quickly. This helps you create more functionality with less code. 
- Mix and match authorization workflows (Group and user based)
- Create a GraphQL endpoint and a schema validating ORM with the same code.
- Authentication collections, indexes, user-defined functions, and roles included.
- Generic CRUD user-defined functions included

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
    - [Fields](#fields)
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
Both of the code samples below will create a new user, group, and users_groups (many-to-many relationship through collection) record.
```python
from pfunk.contrib.auth.collections import Group, User
group = Group.create(name='base', slug='base')
# Example 1: This code calls the Fauna user defined function "create_user" 
# and it can be called with the autogenerated "publc" role 
user = User.create_user(username='goat23', first_name='Michael', last_name='Jordan', email='goat@example.com',  
                        account_status='ACTIVE', password='cruelpass', groups=[group])

# Example 2: You could also create a user with the following code
user = User.create(username='notthegoat', first_name='Lebron', last_name='James',
                   email='notthegoat@gmail.com', account_status='ACTIVE', groups=[group],
                   _credentials={'password': 'hewillneverbethegoat'})
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

Let's delete the record from above.

```python
video.delete()
```

## API Reference

### Collections

If you're not familiar with Fauna, collections are equivalent to tables in a relational database. 

#### Examples

Let's create the collections for a school application. Below we are using subclasses to reduce code.
Some of the most powerful features of ```pfunk``` are displayed in the following code.

```python
from pfunk import (Collection, StringField, EmailField, BooleanField, EnumField,
                   IntegerField, SlugField, ReferenceField, ManyToManyField, Enum,
                   Database)
from pfunk.contrib.auth.collections import User, Group
from pfunk.contrib.auth.resources import GenericUserBasedRole, GenericGroupBasedRole

MAGNET_SCHOOL_TYPES = Enum(name='MagnetSchoolTypes', choices=['art', 'math-science'])

# Create a database instance. Ideally you would do this in a separate module (ex. db.py)
db = Database(name='education')

class UtilCollection(Collection):
    _roles = [GenericGroupBasedRole, GenericUserBasedRole] # We don't have to choose one authorization workflow so let's choose both user and group based.
    created_by = ReferenceField(User)
    group = ReferenceField(Group, required=False)
    
    
class NameSlugCollection(UtilCollection):
    name = StringField(required=True)
    slug = SlugField(required=True, unique=True)
    
    def __unicode__(self):
        return self.name
    
    
class District(NameSlugCollection):
    county = StringField(required=True)
    state = StringField(required=True)
    
    
class Student(UtilCollection):
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    email = EmailField(required=True)
    
    def __unicode__(self):
        return f"{self.first_name} {self.last_name}"
    
    
class School(NameSlugCollection):
    school_email = EmailField(required=False)
    magnet_school = BooleanField(default_value=False)
    magnet_school_type = EnumField(MAGNET_SCHOOL_TYPES, required=False)
    enrollment_population = IntegerField(required=True)
    district = ReferenceField(District)
    students = ManyToManyField(Student)

# Let's add the non-abstract collections to the Database class and publish. 
# Ideally this would be done in another module (ex. db.py). 
# It would probably be a good idea to do this in the same module that the Database instance is created. 
db.add_resources([District, Student, School, User, Group])

# Publish the GraphQL schema, indexes, roles, user defined functions, and the collections.
db.publish()
```
### Fields
If you are familiar with Django models you will understand this section quickly. Fields are probably the smallest building block in ```pfunk```. There are different types of that have different validation.
#### Base Arguments

##### required
This argument signals whether the field needs a value in order for the collection to pass the validation check.
This argument needs to be a boolean (True or False).

##### unique
This argument creates a unique index that makes Fauna throw a validation error if you try to save a new record with the same value for this field.
This argument needs to be a boolean (True or False).

##### default_value
This argument gives the field a default value.

#### BooleanField
This field checks for True or False values.

##### Example

```python
magnet_school = BooleanField(default_value=False)
```

#### EmailField
This field makes sure the value is a valid email address format.

```python
email = EmailField(required=True, unique=True)
```

#### EnumField
This field validates against a given list of values defined in a Enum class. 
That Enum, and it's relationship is translated in the GraphQL on publish.

##### Field Specific Arguments

- **enum** (positional argument) - The Enum instance that contains the name of the ```Enum``` and the choices
##### Example
```python
from pfunk import Enum, EnumField

MAGNET_SCHOOL_TYPES = Enum(name='MagnetSchoolTypes', choices=['art', 'math-science'])
# This should be part of a Collection class but for documentation 
# purposes it's just out in the wild.
magnet_school_type = EnumField(MAGNET_SCHOOL_TYPES, required=False)
```
#### IntegerField
This field validates that the value is an integer.

##### Example

```python
enrollment_population = IntegerField(required=True)
```

#### ManyToManyField
This field validates a list of instances of foreign classes.

##### Field Specific Arguments
- **foreign_class** (positional argument) - The foreign collection non-instantiated class

##### Example
```python
students = ManyToManyField(Student)
```
#### ReferenceField

This field validates a single instance of a foreign classes.

##### Field Specific Arguments
- **foreign_class** (positional argument) - The foreign collection non-instantiated class

##### Example
```python
district = ReferenceField(District)
```
#### SlugField

This field validates a ```slug``` value. An example of a slug value is ```pfunk-is-a-cool-value

##### Example

```python

slug = SlugField(unique=True, required=True)
```

#### StringField
This is the most common field in ```pfunk```, it validates a string value.

##### Example

```python
name = StringField(required=True)
```

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


## Project Short Term Roadmap

### ManyToManyField helper methods

### URLField

### StreetAddressField

