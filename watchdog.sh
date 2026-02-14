#!/bin/bash
LAST=$(cat /tmp/activity.last 2>/dev/null || echo 0)
NOW=$(date +%s)
if [ $((NOW - LAST)) -gt 300 ]; then
  echo "Inactive → shutting down"
  docker compose down
fi