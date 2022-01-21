from pfunk import Collection, StringField, EnumField, Enum, ReferenceField, SlugField
from pfunk.resources import Index
from pfunk.contrib.auth.collections import User, Group
from pfunk.contrib.auth.resources import GenericGroupBasedRole, GenericUserBasedRole

GENDER_PRONOUN = Enum(name='gender_pronouns', choices=['he', 'her', 'they'])


class SimpleIndex(Index):
    name = 'simple-index'
    terms = ['name', 'slug']
    unique = True
    source = 'Project'


class Sport(Collection):
    use_crud_functions = True
    name = StringField(required=True)
    slug = SlugField()

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = [('name', 'slug')]


class Person(Collection):
    collection_roles = [GenericGroupBasedRole]
    verbose_plural_name = 'people'
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    gender_pronoun = EnumField(GENDER_PRONOUN)
    sport = ReferenceField(Sport)
    group = ReferenceField(Group)

    def __unicode__(self):
        return f"{self.first_name} {self.last_name}"


class House(Collection):
    collection_roles = [GenericUserBasedRole]
    address = StringField(required=True)
    user = ReferenceField(User)

    def __unicode__(self):
        return self.address