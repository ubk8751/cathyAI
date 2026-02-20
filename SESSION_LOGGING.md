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
  "ts": 1704067200000,
  "source": "chainlit",
  "session_id": "chainlit:abc123",
  "person_id": "p_me",
  "char_id": "char_cathy",
  "external_user_id": "chainlit:username:ubk8751",
  "sender": "user",
  "text": "How are you today?",
  "len": 18
}
```

```json
{
  "ts": 1704067205000,
  "source": "chainlit",
  "session_id": "chainlit:abc123",
  "person_id": "p_me",
  "char_id": "char_cathy",
  "external_user_id": "chainlit:username:ubk8751",
  "sender": "assistant",
  "text": "I'm doing well, Sam! How about you?",
  "len": 36
}
```

```json
{
  "ts": 1704067210000,
  "source": "chainlit",
  "session_id": "chainlit:abc123",
  "person_id": "p_me",
  "char_id": "char_cathy",
  "external_user_id": "chainlit:username:ubk8751",
  "sender": "system",
  "text": "session_end",
  "len": 11
}
```

### Key Fields

- **ts** - Unix timestamp in milliseconds
- **source** - Always "chainlit" for web UI messages
- **session_id** - Unique session identifier (format: `chainlit:<uuid>`)
- **person_id** - Resolved from identity API (e.g., `p_me`)
- **char_id** - Character identifier (e.g., `char_cathy`)
- **external_user_id** - External identity (e.g., `chainlit:username:ubk8751`)
- **sender** - Either "user", "assistant", or "system"
- **text** - Message content
- **len** - Message length in characters

## Reliability Features

1. **Graceful Failure** - Logging errors are caught and logged as warnings, never crash chat
2. **Automatic Directory Creation** - Creates nested directories as needed
3. **Safe Filenames** - Replaces `:` with `_` in session IDs for filesystem compatibility
4. **UTF-8 Encoding** - Supports all Unicode characters

## Current Behavior

- Events are appended in real-time as messages are sent/received
- Session start logged when chat begins
- Session end logged when chat closes (tab closed or session ended)
- Files persist across container restarts (via `/state` volume mount)
- No rotation or cleanup (handled by future diary distillation process)
- Per-session HTTP client cleanup prevents connection leaks

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
{"ts":1704067200000,"source":"chainlit","session_id":"chainlit:abc123","person_id":"p_me","char_id":"char_cathy","external_user_id":"chainlit:username:ubk8751","sender":"system","text":"session_start character=char_cathy","len":33}
{"ts":1704067205000,"source":"chainlit","session_id":"chainlit:abc123","person_id":"p_me","char_id":"char_cathy","external_user_id":"chainlit:username:ubk8751","sender":"user","text":"Hello!","len":6}
{"ts":1704067210000,"source":"chainlit","session_id":"chainlit:abc123","person_id":"p_me","char_id":"char_cathy","external_user_id":"chainlit:username:ubk8751","sender":"assistant","text":"Hi Sam! How can I help you today?","len":34}
{"ts":1704067215000,"source":"chainlit","session_id":"chainlit:abc123","person_id":"p_me","char_id":"char_cathy","external_user_id":"chainlit:username:ubk8751","sender":"system","text":"session_end","len":11}
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
