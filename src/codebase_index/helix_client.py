import helix
from helix.client import hnswinsert, hnswsearch
from helix.loader import Schema
from helix.mcp import MCPServer

schema = Schema()

db_client = helix.Client(local=True, verbose=True)
mcp = MCPServer("helix-mcp", db_client)
mcp.run()
