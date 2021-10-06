class Event(object):
    """ List of events that can be attached to a View 
    
    Attributes:
        collection (`collection`, required): Fauna Collection
    """
    event_keys: list

    def __init__(self, collection):
        self.collection = collection


class S3Event(Event):
    pass


class SQSEvent(Event):
    event_keys: list = ['Records']


