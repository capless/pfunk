from graphql import parse


class GQLQuery(object):

    def __init__(self, q):
        self.q = q
        self.parse()

    def parse(self):
        p = parse(self.q).definitions[0]
        qq = p.selection_set.selections[0]
        name = qq.name.value
        operation_type = p.operation.value
        try:
            fields = [i.name.value for i in qq.selection_set.selections[0].selection_set.selections]
        except AttributeError:
            fields = []
        self.name = name
        self.fields = fields
        self.operation_type = operation_type