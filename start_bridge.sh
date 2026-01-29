#!/bin/bash
# BlenderVibeBridge Startup Script

echo "--- Starting BlenderVibeBridge MCP Server ---"
cd mcp-server
python3 server.py > ../server.log 2>&1 &
MCP_PID=$!

echo "Server started with PID: $MCP_PID"
echo "Logs are being written to server.log"
echo "Bridge is ready. Please ensure Blender is running the Vibe Bridge addon on port 22000."

# Wait for PID
wait $MCP_PID
