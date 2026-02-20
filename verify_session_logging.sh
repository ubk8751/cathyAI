#!/bin/bash
# Session Logging Verification Script

set -e

echo "=== Session Logging Verification ==="
echo ""

# Check if state directory exists
echo "1. Checking /state directory..."
if docker-compose exec webbui_chat sh -c '[ -d /state ]'; then
    echo "   ✓ /state directory exists"
else
    echo "   ✗ /state directory not found"
    exit 1
fi

# Check write permissions
echo ""
echo "2. Checking write permissions..."
if docker-compose exec webbui_chat sh -c 'touch /state/.write_test && rm /state/.write_test'; then
    echo "   ✓ Write permissions OK"
else
    echo "   ✗ Cannot write to /state"
    exit 1
fi

# Check for session logs
echo ""
echo "3. Checking for session logs..."
SESSION_COUNT=$(docker-compose exec webbui_chat sh -c 'find /state/sessions -name "*.ndjson" 2>/dev/null | wc -l' | tr -d '\r')
if [ "$SESSION_COUNT" -gt 0 ]; then
    echo "   ✓ Found $SESSION_COUNT session log file(s)"
    echo ""
    echo "4. Sample log entries:"
    docker-compose exec webbui_chat sh -c 'find /state/sessions -name "*.ndjson" -exec head -3 {} \; 2>/dev/null' | head -10
else
    echo "   ⚠ No session logs found yet (start a chat to create logs)"
fi

echo ""
echo "5. Session log structure:"
docker-compose exec webbui_chat sh -c 'ls -lR /state/sessions 2>/dev/null || echo "No sessions directory yet"'

echo ""
echo "=== Verification Complete ==="
echo ""
echo "To test:"
echo "1. Open http://localhost:8000"
echo "2. Login and start a chat"
echo "3. Send a few messages"
echo "4. Close the tab"
echo "5. Run this script again to see logs"
