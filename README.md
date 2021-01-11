# PFunk
A Python library to make writing applications with FaunaDB easier. Includes GraphQL integrations.
## Github URL
[https://github.com/capless/pfunk](https://github.com/capless/pfunk)
 
## Getting Started

### Installation
```pip install pfunk```

### Example Usage
Setup the Connection
```python
from pfunk.loading import PFunkHandler

pfunk_handler = PFunkHandler({
    'default': {
        'account_secret_key': 'your-account-secret-key',
        'database_secret_key': 'your-database-secret-key'
    }
})
```

### Define your Models (collections.py) 
```python
from pfunk import Collection, EnumField, StringField

# The handler from the “Setup the Connection” section
from .loading import pfunk_handler

class Person(Collection):
    name = StringField(required=True)
    email = StringField(required=True)
    gender = EnumField(choices=['female', 'male'])
    
    class Meta:
        use_db = 'default'
        handler = pfunk_handler
        # This should create a simple index in the GraphQL template
        default_all_index = True

    def __str__(self):
        return self.name
```

## Authentication (authentication.py)

```python
#From Headers
from pfunk.authentication import faunaclient_from_headers
faunaclient_from_headers({'authorization':'YOUR_AUTH_KEY'})

#From Cookies
from pfunk.authentication import faunaclient_from_cookies
faunaclient_from_cookies(headers = {'cookie':'YOUR_COOKIE'})
```

### OR

```python
from pfunk.auth import authentication

authentication(
            mode = "header" # Determines the source (ie. from headers/cookies)
            source = {'authorization':'YOUR_AUTH_KEY'}
            )

```

## Indexes

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

## Roles

```python
SAMPLE_ROLE = {
            "name": "sample_role",
            "privileges": [
                {
                    "resource": create_function("sample_function"),
                    "actions": {
                        "call": True
                        }
                },
            ]
        }


from pfunk.roles import create_role_from_dict
create_role_from_dict(fauna_client, SAMPLE_ROLE)
```
### OR

```python
from pfunk.roles import create_role_from_kwargs
create_role_from_kwargs(
            fauna_client,
            name="sample_role",
            privileges=[
                 {
                    "resource": create_function("sample_function"),
                    "actions": {
                        "call": True
                        }
                },
            ]
        )

```

## Functions

```python
SAMPLE_FUNCTION = {
            "name": "sample_function",
            "source": q.collection("Sample"),
            "terms": [
                {"field": ["data", "hello"]}
            ],
            "values": [
                {"field": ["data", "world"]}
            ]
        }

from pfunk.functions import create_function_from_dict
create_function_from_dict(
            fauna_client,
            name="sample_function",
            SAMPLE_FUNCTION
        )
```
### OR

```python
from pfunk.functions import create_function_from_kwargs
create_function_from_kwargs(
            fauna_client,
            name = "sample_function",
            source = q.collection("Sample")
            terms = [
                {"field": ["data", "hello"]}
            ],
            values = [
                {"field": ["data", "world"]}
            ]
        )
```

