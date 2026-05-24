#!/bin/sh
# Fix volume permissions so the node user can write to the mounted path
DATA_DIR="${N8N_USER_FOLDER:-/home/node/.n8n}"
mkdir -p "$DATA_DIR"
chown -R node:node "$DATA_DIR" 2>/dev/null || true
chmod -R 755 "$DATA_DIR" 2>/dev/null || true
exec su-exec node n8n "$@"
