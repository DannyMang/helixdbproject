#!/bin/bash
apt-get update && apt-get install -y pkg-config libssl-dev

curl -sSL https://install.helix-db.com | bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
source ~/.bashrc

helix install
helix update
helix deploy --path ./src/helix/helix_config

echo "Starting MCP server..."
uv pip install fastmcp helix-py
nohup fastmcp run src/helix/mcp_server.py --transport http --host 0.0.0.0 --port 8001 > mcp_server.log 2>&1 &

sleep 3

docker compose up --build

tail -f /dev/null
