#!/bin/bash

set -e

if [ -z "$FASTAPI_DOMAIN" ]
then
    # If DOMAIN is blank, set to localhost
    # Note: in prod, domain will be the actual domain
    export FASTAPI_DOMAIN="localhost"
    export LETTA_DOMAIN="letta.wache.dev"
    export HELIX_DOMAIN="helix.wache.dev"
fi

caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
