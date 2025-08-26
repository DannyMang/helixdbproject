import helix
from helix.client import hnswinsert, hnswsearch
from helix.loader import Schema

schema = Schema()

db = helix.Client(local=True, verbose=True)
