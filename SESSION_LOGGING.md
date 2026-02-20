# Session Logging - Foundation for RAG

## Overview

Session logging captures all conversation events to persistent NDJSON files, providing the foundation for:
- Short-term conversation buffer
- Daily distillation into diary entries
- Vector embeddings for RAG retrieval
- Long-term memory across sessions

## Implementation

### File Structure

```
/state/sessions/<person_id>/<char_id>/<session_id>.ndjson
```

Example:
```
/state/sessions/p_me/char_cathy/chainlit_abc123.ndjson
```

### Event Format

Each line is a JSON event:

```json
{
  "ts": 1704067200,
  "source": "chainlit",
  "session_id": "chainlit:abc123",
  "person_id": "p_me",
  "char_id": "char_cathy",
  "sender": "user",
  "text": "How are you today?"
}
```

```json
{
  "ts": 1704067205,
  "source": "chainlit",
  "session_id": "chainlit:abc123",
  "person_id": "p_me",
  "char_id": "char_cathy",
  "sender": "assistant",
  "text": "I'm doing well, Sam! How about you?"
}
```

### Key Fields

- **ts** - Unix timestamp (seconds)
- **source** - Always "chainlit" for web UI messages
- **session_id** - Unique session identifier (format: `chainlit:<uuid>`)
- **person_id** - Resolved from identity API (e.g., `p_me`)
- **char_id** - Character identifier (e.g., `char_cathy`)
- **sender** - Either "user" or "assistant"
- **text** - Message content

## Reliability Features

1. **Graceful Failure** - Logging errors are caught and logged as warnings, never crash chat
2. **Automatic Directory Creation** - Creates nested directories as needed
3. **Safe Filenames** - Replaces `:` with `_` in session IDs for filesystem compatibility
4. **UTF-8 Encoding** - Supports all Unicode characters

## Current Behavior

- Events are appended in real-time as messages are sent/received
- Files persist across container restarts (via `/state` volume mount)
- No rotation or cleanup (handled by future diary distillation process)

## Next Steps

### 1. Daily Distillation Service

Create a separate service that:
- Reads NDJSON session logs
- Groups by person_id + char_id + date
- Generates diary entries: `/state/diary/<person_id>/<char_id>/YYYY-MM-DD.md`
- Marks processed sessions (or deletes old logs)

### 2. Short-Term Memory Buffer

In `app.py`, add:
- Load last N events from recent sessions
- Inject summary into system prompt
- Example: "Recent context: Yesterday you discussed [topic]..."

### 3. Vector Embeddings for RAG

- Embed diary entries (not raw events)
- Store in `/state/index/<person_id>/<char_id>.sqlite` or vector DB
- Query on chat start for relevant memories

### 4. Cross-Character Memory

- Some memories should be character-agnostic
- Store in `/state/diary/<person_id>/_shared/`
- Example: User's preferences, life events, relationships

## Testing

```bash
# Start a chat session and send messages
# Then check the logs:

docker-compose exec webbui_chat sh -c 'ls -lR /state/sessions/'

# View a session log:
docker-compose exec webbui_chat sh -c 'cat /state/sessions/p_me/*/chainlit_*.ndjson'
```

Expected output:
```json
{"ts":1704067200,"source":"chainlit","session_id":"chainlit:abc123","person_id":"p_me","char_id":"char_cathy","sender":"user","text":"Hello!"}
{"ts":1704067205,"source":"chainlit","session_id":"chainlit:abc123","person_id":"p_me","char_id":"char_cathy","sender":"assistant","text":"Hi Sam! How can I help you today?"}
```

## Volume Mount Verification

Your `docker-compose.yaml` already has:

```yaml
volumes:
  - ./state:/state
```

This ensures:
- Session logs persist across container rebuilds
- Diary files will be accessible from host
- Future services can read/write the same `/state` directory

## Error Handling

If logging fails (disk full, permissions, etc.):
- Warning logged: `Failed to append event: <error>`
- Chat continues normally
- No user-visible error

This ensures logging never disrupts the user experience.
