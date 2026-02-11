#!/bin/bash
exec 2>/tmp/mcp-debug.log
echo "=== MCP Start $(date) ===" >&2
echo "Python: $(/opt/greiner-portal/venv/bin/python3 --version)" >&2
echo "Starting server..." >&2
exec /opt/greiner-portal/venv/bin/python3 -u /opt/greiner-portal/scripts/mcp/server.py 2>>/tmp/mcp-debug.log
