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
from pfunk.client import Handler

handler = Handler({
    'default': {
        'secret': 'your-account-secret-key',
    }
})
```

### Define your Collections (collections.py) 
```python
from pfunk import Collection, EnumField, StringField

# The handler from the “Setup the Connection” section
from .loading import handler

class Person(Collection):
    name = StringField(required=True)
    email = StringField(required=True)
    gender = EnumField(choices=['female', 'male'])
    
    class Meta:
        use_db = 'default'
        handler = handler
        # This should create a simple index in the GraphQL template
        default_all_index = True

    def __str__(self):
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
