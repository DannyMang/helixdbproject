#!/bin/bash
set -e


# Wait for service to be ready
sleep 2

echo "Clearing old deployments..."
helix stop --all || echo "No deployments to stop"

echo "Deploying new configuration..."
helix deploy --path /app/helix_config --port 6969

echo "Starting Helix MCP server"
fastmcp run mcp_server.py

wait
