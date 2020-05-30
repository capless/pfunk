from faunadb.client import FaunaClient
from faunadb import query as q
from envs import env


super_client = FaunaClient(secret=env('FAUNA_SUPER_SECRET'))

client = FaunaClient(secret=env('FAUNA_SECRET'))