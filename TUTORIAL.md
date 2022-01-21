# Tutorial

In this tutorial we'll show you how to create a simple PFunk project. Let's call our project **SchoolZone**, a 
demo app for tracking students and teachers in a school. 

## Step 1: Create New Project

Let's use the PFunk CLI to create a new project.

```python
pfunk init schoolzone
```

## Step 2: Create Collections

Let's create some collections to store our data in. If you're new to Fauna, collections are the equivalent to tables in 
relational database. 

```python
from pfunk.collection import Collection
from pfunk.fields import StringField, IntegerField, ReferenceField, ManyToManyField
from pfunk.contrib.auth.collections import User, Group
from pfunk.contrib.auth.resources import GenericGroupBasedRole


class School(Collection):
    collection_roles = [GenericGroupBasedRole]
    name = StringField(required=True)
    address = StringField(required=False)
    group = ReferenceField(Group, required=True)
    

class Teacher(Collection):
    collection_roles = [GenericGroupBasedRole]
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    group = ReferenceField(Group, required=True)
    

class Class(Collection):
    collection_roles = [GenericGroupBasedRole]
    name = StringField(required=True)
    teacher = ReferenceField(Teacher)
    group = ReferenceField(Group, required=True)
    

class Student(Collection):
    collection_roles = [GenericGroupBasedRole]
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    grade = IntegerField(required=True)
    group = ReferenceField(Group, required=True)
    
    
class StudentClass(Collection):
    collection_roles = [GenericGroupBasedRole]
    class_ref = ReferenceField(Class)
    student_ref = ReferenceField(Student)
    final_grade = IntegerField(required=False)
    absences = IntegerField()
    tardies = IntegerField()
    group = ReferenceField(Group, required=True)
    
        

```
## Step 3: Add Collections to Project

Open `schoolzone/project.py` and add the collections.

```python

from pfunk import Project
from pfunk.contrib.auth.collections import Key
from .collections import School, Teacher, Class, Student, StudentClass, User, Group


project = Project(_collections=[User, Group, School, Teacher, Class, Student, StudentClass])
```

## Step 4: Seed Keys

PFunk uses encrypted JWTs with private keys that unencrypt the JWT during request/response loop. We need to seed the keys.

```commandline
pfunk seed_keys staging
```

## Step 5: Run the Local Server

Next, we run the local server to test things out.

```commandline
pfunk local
```

## Step 6: Deploy

Publish the GraphQL schema to Fauna and deploy the API to Lambda and API Gateway.

```commandline
pfunk deploy staging
```

If you don't want to deploy the API and just want to publish the GraphQL schema to Fauna.

```commandline
pfunk publish staging
```