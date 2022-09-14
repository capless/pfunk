![Pfunk logo](https://qwigocom.b-cdn.net/opensource/images/pfunk.png?width=160 "Pfunk")

A Python library to make writing applications with FaunaDB easier. 
Includes GraphQL and generic ABAC auth workflow integrations.

## Key Features
- DRY (Don't Repeat Yourself) code to help you create multiple collections, indexes, roles, and user-defined functions 
  quickly. This helps you create more functionality with less code. 
- Mix and match authorization workflows (Group and user based)
- Group level permissions
- Create a GraphQL endpoint and a schema validating ORM with the same code.
- Authentication collections, indexes, user-defined functions, and roles included.
- Generic CRUD user-defined functions included
- Create a REST API to integrate Fauna and Non-Fauna related tasks
- Schema validation based on the [Valley](https://github.com/capless/valley) library.

## Full Documentation

[Documentation](https://pfunk.carcamp.dev/docs/pfunk.html)

## Table of Contents

- [Getting Started](#Getting-Started)
    - [Installation](#Installation)
    - [Environment Variables](#environment-variables)
    - [Setup the Connection](#setup-the-connection)
    - [Define your Collections](#define-your-collections-collectionspy)
    - [Choose an Auth Workflow](#auth-workflows)
    - [Publish](#publish)
    - [Save Some Data](#save-some-data)
    - [Query Your Data](#query-your-data)
    - [Delete a Record](#delete-a-record)
        


### Getting Started

### Installation
```pip install pfunk```

### Environment Variables

- **FAUNA_SECRET** - Fauna admin or server key.
- **FAUNA_SCHEME** - (optional) HTTP scheme to use (default: https)
- 
### Setup the Connection

#### Using Environment Variables (Preferred Method)

If you can easily set environment variables just set the ```FAUNA_SECRET``` environment variable to your key.

### Define your Collections (collections.py)

For an example project let's create a project management app. 

```python
from pfunk import (Collection, StringField, ReferenceField, DateField,
                   Project, Enum, EnumField, IntegerField, FloatField,
                  SlugField)
from pfunk.contrib.auth.collections import User, Group
from pfunk.contrib.auth.resources import GenericGroupBasedRole, GenericUserBasedRole



STATUS = Enum(name='ProductStatus', choices=['unstarted', 'started', 'completed', 'delivered'])


class AbstractGroupCollection(Collection):
    """
    Abstract Collection very similar to abstract models in Django. 
    The main difference is you don't have to add abstract=True in the Meta class.
    """
    # Here we are defining the roles that should be 
    # created for this collection (by proxy this role will be applied 
    # to its subclasses. We could however change the list of roles below.
    collection_roles = [GenericGroupBasedRole]
    title = StringField(required=True)
    group = ReferenceField(Group, required=True)
    
    def __unicode__(self):
        return self.title
    
    
class Product(AbstractGroupCollection):
    slug = SlugField(required=True)
    description = StringField()
    due_date = DateField(required=False)
    
    class Meta:
        """
        Add unique together index to ensure that the same slug is not used 
        for more than one product that belongs to a group. Similar to the
        Github's repo naming convention ex. https://github.com/capless/pfunk. 
        In that example 'capless' is the group slug and 'pfunk' is the 
        product's slug
        """
        unique_together = ('slug', 'group')
    
    
class Sprint(AbstractGroupCollection):
    product = ReferenceField(Product, required=True)
    start_date = DateField(required=True)
    end_date = DateField(required=True)
    
    
class Story(AbstractGroupCollection):
    description = StringField()
    points = IntegerField()
    product = ReferenceField(Product, required=True)
    sprint = ReferenceField(Sprint, required=False)
    status = EnumField(STATUS)
    

# Create a Project
project = Project()

# Add Collections to the Project
project.add_resources([User, Group, Product, Story, Sprint])

```
### Auth Workflows

In the example above, the ```collection_roles``` list on the ```Collection``` classes attaches generic roles to the 
collection.  Currently, you can choose a **group based** workflow, **user based**, or a **mix** of the two.

#### User Based Role

This role allows you to create, read, write, and delete documents that you haveyou are the owner of. The `user` field determines if you are the owner.

#### Group Based Role

This role allows you to create, read, write, and delete documents if both of the following conditions are true: 

1. You belong to the group that owns the document
2. You have the create permission to perform the action (`create`, `read`, `write`, and `delete`) 

### Publish

```python
project.publish()
```

### Create Group and User
Both of the code samples below will create a new user, group, and users_groups (many-to-many relationship through collection) record.
```python
from pfunk.contrib.auth.collections import Group, User
group = Group.create(name='base', slug='base')

# Example 2: You could also create a user with the following code
user = User.create(username='notthegoat', first_name='Lebron', last_name='James',
                   email='notthegoat@gmail.com', account_status='ACTIVE', groups=[group],
                   _credentials='hewillneverbethegoat')

```

### Give User New Permissions

```python
# User instance from above (username: notthegoat)
user.add_permissions(group, ['create', 'read', 'write', 'delete'])
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


product = Product.create(
    title='PFunk Project',
    slug='pfunk',
    description='Some example project for test Pfunk',
    group=group,
    _token=token #The token gained in the previous step. If you do not specify a token here it defaults to the key used in the FAUNA_SECRET env.
)

```

### Query your Data
Let's get the video you just created.

```python
product = Product.get('the-key-for-the-previous-video', _token=token)
```

Let's query for all videos using the server key.

```python
products = Products.all()
```

Let's query for all videos that the logged in user has access to.

```python

products = Products.all(_token=token)
```

### Delete a Record

Let's delete the record from above.

```python
product.delete()
```
