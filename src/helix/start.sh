#!/bin/bash
set -e

echo "Starting Helix service..."
helix start --daemon &

# Wait for service to be ready
sleep 2

echo "Clearing old deployments..."
helix stop --all || echo "No deployments to stop"

echo "Deploying new configuration..."
exec helix deploy --path /app/helix_config --foreground
