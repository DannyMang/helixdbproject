# A client for interacting
import os
from dotenv import load_dotenv
from letta_client import Letta

load_dotenv()
LETTA_API_KEY = os.getenv("LETTA_API_KEY")
AGENT_ID = "agent-0042f472-b5a4-452f-8be1-d69f0cb91d22"

client = Letta(token=LETTA_API_KEY, project="Toph")

def get_letta_agent(user_id: str):
    agent = client.agents.retrieve(agent_id=AGENT_ID)
    all_memory_blocks = client.blocks.list()
    for memory_block in all_memory_blocks:
        if memory_block.label.startswith(user_id):
            agent.blocks.attach(agent_id=AGENT_ID, block_id=memory_block.id)

    return agent

def create_memory_block(value: str, user_id: str):
    client.blocks.create(value=value, label=f"{user_id}_memory_block")

def cleanup_agent_memory_blocks(user_id: str):
    blocks = client.agents.blocks.list(agent_id=AGENT_ID)
    for block in blocks:
        if block.label.startswith(user_id):
            client.agents.block.detach(
                agent_id=AGENT_ID,
                block_id=block.id
            )
