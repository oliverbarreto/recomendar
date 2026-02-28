#!/bin/bash

# Claude Code Session Logger
# Captures conversation content and saves to docs/sessions/

# Get project root directory
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SESSIONS_DIR="$PROJECT_ROOT/docs/sessions"
DEBUG_FILE="$SESSIONS_DIR/debug.log"

# Ensure sessions directory exists
mkdir -p "$SESSIONS_DIR"

# Function to log debug information
debug_log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$DEBUG_FILE"
}

# Log that hook was triggered
debug_log "Hook triggered with args: $*"
debug_log "CLAUDE_PROJECT_DIR: $CLAUDE_PROJECT_DIR"
debug_log "CLAUDE_FILE_PATHS: $CLAUDE_FILE_PATHS"
debug_log "CLAUDE_TOOL_OUTPUT: $CLAUDE_TOOL_OUTPUT"

# Read JSON data from stdin if available
JSON_DATA=""
if [ ! -t 0 ]; then
    JSON_DATA=$(cat)
    debug_log "JSON input: $JSON_DATA"
fi

# Get current timestamp
TIMESTAMP=$(date "+%Y-%m-%d_%H-%M-%S")
SESSION_FILE="$SESSIONS_DIR/${TIMESTAMP}_session.md"

# Function to append to session file
append_to_session() {
    echo "$1" >> "$SESSION_FILE"
}

# Function to get or create session file for today
get_session_file() {
    # Use today's date for session file
    TODAY=$(date "+%Y-%m-%d")

    # Find existing session file for today or create new one
    EXISTING_SESSION=$(ls "$SESSIONS_DIR"/${TODAY}_*_session.md 2>/dev/null | head -1)

    if [ -n "$EXISTING_SESSION" ]; then
        SESSION_FILE="$EXISTING_SESSION"
        debug_log "Using existing session file: $SESSION_FILE"
    else
        SESSION_FILE="$SESSIONS_DIR/${TODAY}_$(date "+%H-%M-%S")_session.md"
        debug_log "Creating new session file: $SESSION_FILE"
        # Initialize new session file
        cat > "$SESSION_FILE" << EOF
# Claude Code Session - $(date "+%Y-%m-%d %H:%M:%S")

EOF
    fi
}

# Parse JSON data to extract relevant information
extract_from_json() {
    local key="$1"
    if [ -n "$JSON_DATA" ]; then
        echo "$JSON_DATA" | grep -o "\"$key\":[^,}]*" | sed "s/\"$key\":\"//" | sed 's/"$//'
    fi
}

# Extract nested JSON values (for tool_input.command, tool_input.description, etc.)
extract_nested_json() {
    local path="$1"
    if [ -n "$JSON_DATA" ]; then
        echo "$JSON_DATA" | python3 -c "
import json
import sys
try:
    data = json.load(sys.stdin)
    keys = '$path'.split('.')
    result = data
    for key in keys:
        if key in result:
            result = result[key]
        else:
            result = ''
            break
    if isinstance(result, str):
        print(result)
    elif isinstance(result, dict) or isinstance(result, list):
        print(json.dumps(result, separators=(',', ':')))
    else:
        print(str(result))
except:
    pass
" <<< "$JSON_DATA"
    fi
}

# Get assistant text content from transcript
get_assistant_content() {
    local transcript_path="$1"
    if [ -n "$transcript_path" ] && [ -f "$transcript_path" ]; then
        debug_log "Parsing assistant content from transcript: $transcript_path"

        # Extract assistant messages with text content from the last few entries
        python3 -c "
import json
import sys

try:
    with open('$transcript_path', 'r') as f:
        lines = f.readlines()

    # Process last 20 lines to find recent assistant content
    assistant_texts = []
    for line in lines[-20:]:
        try:
            entry = json.loads(line.strip())
            if (entry.get('type') == 'assistant' and
                'message' in entry and
                'content' in entry['message']):

                content_array = entry['message']['content']
                for content_item in content_array:
                    if content_item.get('type') == 'text':
                        text = content_item.get('text', '').strip()
                        if text and text not in assistant_texts:
                            assistant_texts.append(text)
                    elif content_item.get('type') == 'thinking':
                        thinking = content_item.get('thinking', '').strip()
                        if thinking:
                            # Format thinking blocks
                            thinking_lines = thinking.split('\n')
                            formatted_thinking = []
                            for line in thinking_lines:
                                if line.strip():
                                    formatted_thinking.append('  ' + line.strip())
                            if formatted_thinking:
                                assistant_texts.append('✻ Thinking…\n\n' + '\n'.join(formatted_thinking))
        except:
            continue

    # Print the most recent assistant content
    if assistant_texts:
        print(assistant_texts[-1])

except Exception as e:
    pass
"
    fi
}

case "$1" in
    "UserPromptSubmit")
        debug_log "Processing UserPromptSubmit hook"
        get_session_file

        # Extract user prompt from JSON
        USER_PROMPT=$(extract_from_json "prompt")
        if [ -z "$USER_PROMPT" ]; then
            USER_PROMPT="$2"  # Fallback to command line arg
        fi

        append_to_session "### PROMPT"
        echo "$USER_PROMPT" | sed 's/^/> /' >> "$SESSION_FILE"
        append_to_session ""
        append_to_session "### RESULT"
        append_to_session '```'
        ;;

    "PostToolUse")
        debug_log "Processing PostToolUse hook"
        get_session_file

        # Extract tool information from JSON properly
        TOOL_NAME=$(extract_from_json "tool_name")
        TOOL_DESCRIPTION=$(extract_nested_json "tool_input.description")
        TOOL_COMMAND=$(extract_nested_json "tool_input.command")
        TOOL_STDOUT=$(extract_nested_json "tool_response.stdout")
        TOOL_STDERR=$(extract_nested_json "tool_response.stderr")
        TOOL_FILE_PATH=$(extract_nested_json "tool_input.file_path")

        # First, add assistant content if available from transcript
        TRANSCRIPT_PATH=$(extract_from_json "transcript_path")
        if [ -n "$TRANSCRIPT_PATH" ]; then
            ASSISTANT_CONTENT=$(get_assistant_content "$TRANSCRIPT_PATH")
            if [ -n "$ASSISTANT_CONTENT" ]; then
                append_to_session ""
                echo "$ASSISTANT_CONTENT" >> "$SESSION_FILE"
                append_to_session ""
            fi
        fi

        # Format tool execution with Claude Code symbols and description
        if [ -n "$TOOL_NAME" ]; then
            if [ -n "$TOOL_DESCRIPTION" ]; then
                append_to_session "⏺ $TOOL_DESCRIPTION"
            elif [ -n "$TOOL_COMMAND" ]; then
                append_to_session "⏺ $TOOL_NAME($TOOL_COMMAND)"
            elif [ -n "$TOOL_FILE_PATH" ]; then
                append_to_session "⏺ $TOOL_NAME($TOOL_FILE_PATH)"
            else
                append_to_session "⏺ $TOOL_NAME()"
            fi
        else
            append_to_session "⏺ Tool execution"
        fi

        # Format tool result with tree symbol
        if [ -n "$TOOL_STDOUT" ]; then
            echo "$TOOL_STDOUT" | sed 's/^/⎿  /' >> "$SESSION_FILE"
        fi
        if [ -n "$TOOL_STDERR" ] && [ "$TOOL_STDERR" != '""' ]; then
            echo "$TOOL_STDERR" | sed 's/^/⎿  stderr: /' >> "$SESSION_FILE"
        fi
        append_to_session ""
        ;;

    "Stop")
        debug_log "Processing Stop hook"
        get_session_file

        # Try to extract the complete assistant response from transcript
        TRANSCRIPT_PATH=$(extract_from_json "transcript_path")
        if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
            debug_log "Reading final response from transcript: $TRANSCRIPT_PATH"

            # Get all assistant content from this conversation turn
            FINAL_RESPONSE=$(get_assistant_content "$TRANSCRIPT_PATH")
            if [ -n "$FINAL_RESPONSE" ]; then
                debug_log "Found final assistant response in transcript"
                append_to_session ""
                echo "$FINAL_RESPONSE" >> "$SESSION_FILE"
                append_to_session ""
            fi
        fi
        ;;

    "SessionEnd")
        debug_log "Processing SessionEnd hook"
        get_session_file
        append_to_session '```'
        append_to_session ""
        append_to_session "---"
        append_to_session ""
        ;;

    # Legacy support for manual testing
    "start")
        get_session_file
        append_to_session ""
        append_to_session "## SESSION START - $(date "+%H:%M:%S")"
        append_to_session ""
        ;;

    "user")
        get_session_file
        USER_INPUT="$2"
        append_to_session "### PROMPT"
        echo "$USER_INPUT" | sed 's/^/> /' >> "$SESSION_FILE"
        append_to_session ""
        append_to_session "### RESULT"
        append_to_session '```'
        ;;

    "tool")
        get_session_file
        TOOL_NAME="$2"
        TOOL_RESULT="$3"
        append_to_session "⏺ $TOOL_NAME"
        if [ -n "$TOOL_RESULT" ]; then
            echo "$TOOL_RESULT" | sed 's/^/⎿  /' >> "$SESSION_FILE"
        fi
        append_to_session ""
        ;;

    "end")
        get_session_file
        append_to_session '```'
        append_to_session ""
        append_to_session "---"
        append_to_session ""
        ;;

    *)
        debug_log "Unknown hook type: $1"
        echo "Usage: $0 {UserPromptSubmit|PostToolUse|Stop|SessionEnd|start|user|tool|end} [content]"
        exit 1
        ;;
esac