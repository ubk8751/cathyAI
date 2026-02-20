# Identity Resolution Setup

## Overview

The identity resolution feature allows cathyAI to personalize conversations by resolving authenticated usernames to preferred display names via an external identity API.

## How It Works

1. User logs in with their username (e.g., `ubk8751`)
2. Chainlit authenticates against SQLite database
3. On chat start, app calls identity API with `chainlit:username:ubk8751`
4. Identity API returns `{"person_id": "p_me", "preferred_name": "Sam"}`
5. Character addresses user as "Sam" in conversation

## Configuration

Add these two lines to your `.env` file:

```bash
IDENTITY_API_URL=http://192.168.1.59:8092
IDENTITY_API_KEY=your_identity_api_key_here
```

## Identity API Format

The identity API must support:

**Endpoint:** `GET /identity/resolve`

**Query Parameters:**
- `external_id` - The external identifier (format: `chainlit:username:{username}`)

**Headers:**
- `x-api-key` - API authentication key

**Response:**
```json
{
  "person_id": "p_me",
  "preferred_name": "Sam"
}
```

## Behavior

- **Identity API configured:** Characters use preferred names from identity service with strengthened hints
- **Identity API unavailable:** Falls back to username or "there"
- **Anonymous users:** Uses `chainlit:anonymous` as external_id
- **Name enforcement:** System prompt tells model it already knows the user's name

## Testing

After adding the env vars and restarting:

```bash
# Verify env vars are loaded in container
docker-compose exec webbui_chat sh -lc 'echo "$IDENTITY_API_URL" && echo "$IDENTITY_API_KEY" | wc -c'

# Check logs for identity resolution
docker-compose logs -f webbui_chat | grep -i identity
```

Expected log output:
```
INFO: Chat started with character: Cathy for user: ubk8751 (preferred: Sam)
```

### Debug Command: /whoami

Type `/whoami` in the chat to verify identity resolution:

```
external_user_id: chainlit:username:ubk8751
person_id: p_me
preferred_name: Sam
```

This confirms:
- Your username was captured from Chainlit auth
- Identity API resolved it correctly
- Preferred name is injected into system prompt

## No Hardcoding

The implementation dynamically resolves **any** authenticated user:
- `ubk8751` → resolves to whatever you mapped in identity API
- `alice` → resolves to her preferred name
- `bob` → resolves to his preferred name

No usernames are hardcoded in the application.

## Bug Fixes Applied

1. **ETag Cache Fix** - `fetch_character_private` now uses in-memory cache on 304 responses instead of re-fetching
2. **History Fallback** - Preserves identity hint if history is ever reset
3. **Debug Command** - `/whoami` command for quick identity verification

## Next Steps

### 1. Session Logging (Foundation for RAG)

Now that you have stable identity resolution, the next step is to log conversation events:

- Create `/state/sessions/<person_id>/<char_id>/<session_id>.ndjson`
- Append each user message and assistant reply as NDJSON events
- This becomes the foundation for:
  - Short-term conversation buffer
  - Daily distillation
  - Vector embeddings for RAG

### 2. Verify Container Mount

Your `docker-compose.yaml` already mounts `./state:/state`, which is perfect for:
- SQLite user database
- Session logs
- Future diary files

This persists across container rebuilds.
