class Queryset:

    def __init__(self, query_response: dict, cls, lazied=False):
        self.query_response = query_response
        self.data = [cls(_ref=i.get('ref'), _lazied=lazied, **i.get('data')) for i in query_response.get('data', [])]
        if query_response.get('after'):
            self.after = query_response.get('after')[0]
        else:
            self.after = None
        if query_response.get('before'):
            self.before = query_response.get('before')[0]
        else:
            self.before = None

    def to_dict(self):
        return self.query_response

    def __iter__(self):
        return iter(self.data)

    def __next__(self):
        return self

    def __len__(self):
        return len(self.data)

    def __getitem__(self, x):
        return self.data[x]