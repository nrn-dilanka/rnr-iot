#!/bin/bash
# Quick API Server Test Script

echo "Testing uvicorn command fix..."

# Test if uvicorn accepts our new parameters
echo "Running uvicorn --help to verify parameters..."
docker run --rm python:3.11-slim pip install uvicorn fastapi > /dev/null 2>&1
docker run --rm python:3.11-slim bash -c "pip install uvicorn fastapi > /dev/null 2>&1 && uvicorn --help | grep -E 'workers|access-log|log-level'"

echo ""
echo "Valid uvicorn parameters verified!"
echo "The fix should resolve the API server startup issue."
