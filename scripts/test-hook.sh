#!/bin/bash

# Simple test hook to verify Claude Code hooks are working
TEST_LOG="/Users/oliver/Library/Mobile Documents/com~apple~CloudDocs/dev/webaps/labcastarr/docs/sessions/hook-test.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Test hook triggered with event: $1" >> "$TEST_LOG"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] CLAUDE_PROJECT_DIR: $CLAUDE_PROJECT_DIR" >> "$TEST_LOG"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Args: $*" >> "$TEST_LOG"

# Read JSON from stdin if available
if [ ! -t 0 ]; then
    JSON_INPUT=$(cat)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] JSON: $JSON_INPUT" >> "$TEST_LOG"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ---" >> "$TEST_LOG"