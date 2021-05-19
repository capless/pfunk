from pfunk import Collection, StringField, EnumField, Enum, ReferenceField, SlugField


GENDER_PRONOUN = Enum(name='gender_pronouns', choices=['he', 'her', 'they'])


class Sport(Collection):
    name = StringField(required=True)
    slug = SlugField()

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = ['name', 'slug']


class Person(Collection):
    _verbose_plural_name = 'people'
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    gender_pronoun = EnumField(GENDER_PRONOUN)
    sport = ReferenceField(Sport)

    def __unicode__(self):
        return f"{self.first_name} {self.last_name}"