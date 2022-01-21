import inspect

from faunadb.objects import Ref
from valley.utils.json_utils import ValleyEncoder


class PFunkEncoder(ValleyEncoder):
    show_type = False

    def default(self, obj):
        if isinstance(obj, Ref):

            obj_dict = {'id': obj.id(), 'collection': obj.collection().id()}
            if self.show_type:
                obj_dict['_type'] = '{}.{}'.format(inspect.getmodule(obj).__name__, obj.__class__.__name__)
            return obj_dict
        if hasattr(obj, 'get_collection_name'):
            if obj._lazied:
                obj = obj._get(obj.ref.id())
        try:
            return super(PFunkEncoder, self).default(obj)
        except AttributeError:
            return str(obj)