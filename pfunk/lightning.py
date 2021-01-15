from faunadb.client import FaunaClient
from faunadb import query as q
from .collection import Collection


class Lightning:
    """
        SAMPLE CODE:

        class Person(Collection):
            name = StringField(required=True)
            email = StringField(required=True)

            def __str__(self):
                return self.name

        class All_Persons_Index(Index):
            name = 'All-persons'
            source = 'person'
            terms = []
            values = []
            unique = False
            serialized = True

        class Client_Role(Role):
            name = 'All-persons'
            privileges = []
            membership = []

        class Test_DB(Lightning):
            def __init__(key):
                self.person_collection = Person
                self.all_persons_index = All_Persons_Index
                self.client_role = Client_Role

                super().__init__(key)

            def my_custom_fcn(self, data: Person):
                self.add(data).save()
                # Do notify through email


        SAMPLE USAGE:

        SAMPLE_PERSON = Person(name = "John", email = "jdoe@gmail.com")

        #Initiating Pfunk
        test_DB = Test_DB("samplekey")

        # Adding Documents
        test_DB.add(Person(SAMPLE_PERSON)).save()
        # alternatively
        test_DB.add("person_collection", SAMPLE_PERSON)
        test_DB.save_all()

        # Using Indexes
        test_DB.index("all_persons_index")

    """

    def __init__(self, key):
        self.client = FaunaClient(key)

        if self.client.query(q.exists(q.collection("PFUNK_META"))):
            # TODO: GET PFUNK_META
            pass
        else:
            # TODO: CREATE PFUNK_META
            self.client.query(q.create_collection(
                {"name": "PFUNK_META"}))

    def _add_collection(self, collection):
        if not issubclass(collection, Collection):
            raise TypeError('Input parameter is not of type: Collection')
        if issubclass(collection, Collection) and collection not in self._collection_list:
            self._collection_list.append(collection)
            cl = set(self._collection_list)
            self._collection_list = list(cl)

    def _add_index(self, index):
        pass

    def _modify_meta(self, **data):
        pass
