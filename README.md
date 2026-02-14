# cathyAI

A modular AI companion platform with a Chainlit web UI and FastAPI character management service. Features multi-character support, live model switching, and shared character data between services.

## Overview

cathyAI consists of two independent services:

- **webbui_chat** - Chainlit-based chat UI (port 8000)
- **characters_api** - FastAPI character data service (port 8090)

Both services share character configurations and avatars from the root `characters/` and `public/` directories.

## Features

- **Multi-Character Support** - JSON-based characters with avatars, greetings, and system prompts
- **Character API** - RESTful API for character data with file resolution and alias management
- **Live Model Switching** - Dynamic model selection via external API
- **API-Based Architecture** - External chat, model listing, and emotion detection APIs
- **Energy Efficient** - Container shutdown after 5 min inactivity
- **Docker Ready** - Each service has its own docker-compose configuration
- **CI/CD Pipeline** - Automated testing with GitHub Actions

## Project Structure

```
cathyAI/
├── characters/                     # Shared character data
│   ├── *.json                      # Character configurations
│   ├── system_prompt/              # External prompt files
│   └── character_info/             # Character backstories
├── public/avatars/                 # Shared avatar images
├── webbui_chat/                    # Chainlit chat UI service
│   ├── app.py                      # Main application
│   ├── Dockerfile
│   ├── docker-compose.yaml
│   ├── requirements.txt
│   └── .env
├── characters_api/                 # FastAPI character service
│   ├── app.py                      # API endpoints
│   ├── Dockerfile
│   ├── docker-compose.yaml
│   ├── requirements.txt
│   └── .env
├── tests/                          # Test suites
│   ├── test_app.py                 # Shared resource tests
│   ├── test_webbui_chat.py         # Chat UI tests
│   └── test_characters_api.py      # API tests
├── .github/workflows/test.yml      # CI/CD pipeline
├── .env.template                   # Environment template
├── watchdog.sh                     # Inactivity monitor
└── README.md
```

## Shared Resources

### Character Configuration

Add JSON files in `characters/`:

```json
{
  "name": "Character name",
  "nickname": "Optional nickname",
  "avatar": "character_pfp.jpg",
  "greeting": "Hello!",
  "system_prompt": "character.prompt",
  "description": "character.info",
  "model": "llama3.1:8b"
}
```

System prompts can be:
- Inline text starting with "You"
- Filename referencing `characters/system_prompt/*.prompt`

Avatars go in `public/avatars/` and are served by both services.

---

## webbui_chat Service

Chainlit-based chat interface with multi-character profiles and live model switching.

### Setup

```bash
cd webbui_chat

# Configure environment
cp .env.template .env
# Edit .env with your API endpoints

# Docker
docker compose up -d --build

# Local development
pip install -r requirements.txt
chainlit run app.py
```

Access at http://localhost:8000

### Environment Variables

```bash
# Required: External API endpoints
CHAT_API_URL=http://your-api:11434/api/chat
MODELS_API_URL=http://your-api:11434/api/tags

# Optional: Emotion detection
EMOTION_ENABLED=0
EMOTION_API_URL=http://your-api:8001/emotion

# Optional: API authentication
CHAT_API_KEY=
MODELS_API_KEY=
EMOTION_API_KEY=

# Optional: Timeouts (seconds)
CHAT_TIMEOUT=120
MODELS_TIMEOUT=10
EMOTION_TIMEOUT=10
```

### External API Requirements

**Models API (GET)** - Returns list of available models:
```json
{"models": ["modelA", "modelB"]}
```

**Chat API (POST)** - Streaming chat endpoint (Ollama-compatible):
```json
// Request
{"model": "modelA", "messages": [{"role": "user", "content": "Hi"}], "stream": true}

// Response (Ollama NDJSON format)
{"message":{"role":"assistant","content":"Hello"}, "done":false}
{"message":{"role":"assistant","content":"Hello there!"}, "done":true}
```

**Emotion API (POST)** - Optional emotion detection:
```json
// Request
{"text": "I am happy!"}

// Response
{"label": "joy", "score": 0.87}
```

### Features

- Character profile dropdown with avatars
- Live model switching via sidebar
- Streaming chat responses
- Optional emotion detection
- Session-based conversation history
- Activity tracking for watchdog

---

## characters_api Service

FastAPI service providing RESTful access to character data with automatic file resolution.

### Setup

```bash
cd characters_api

# Configure environment
cp .env.template .env
# Edit .env with your settings

# Docker
docker compose up -d --build

# Local development
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8090
```

Access at http://localhost:8090

### Environment Variables

```bash
# Optional: API authentication
CHAR_API_KEY=

# Optional: Public URL for avatar links
HOST_URL=http://192.168.1.58:8090
```

### API Endpoints

**GET /health** - Health check
```json
{"ok": true, "char_dir": "/app/characters", ...}
```

**GET /characters** - List all characters
```json
{
  "characters": [
    {
      "id": "[character_name]",
      "name": "[full_character_name]",
      "nickname": null|[list of alternative names],
      "model": "llama3.1:8b",
      "greeting": "Hello!",
      "avatar": "[id]_pfp.jpg",
      "avatar_url": "http://host:8090/avatars/[id]_pfp.jpg",
      "aliases": [full_list_of_names]
    }
  ]
}
```

**GET /characters/{char_id}** - Get character details
```json
{
  "name": "[full_character_name]",
  "system_prompt": "You are [character]...",
  "character_background": "[character] is...",
  "aliases": [full_list_of_names],
  "avatar_url": "http://host:8090/avatars/[id]_pfp.jpg",
  ...
}
```

**GET /avatars/{filename}** - Serve avatar image

### Features

- Automatic system prompt file resolution
- Character alias generation (name, nickname, ID)
- Avatar URL generation
- Optional API key authentication
- Matrix-specific field support

---

## Testing

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_webbui_chat.py -v
pytest tests/test_characters_api.py -v

# Run specific test
pytest tests/test_app.py::test_character_json_structure
```

Test coverage:
- **test_app.py** - Shared resources (characters, avatars, scripts)
- **test_webbui_chat.py** - Chat UI (Docker, imports, character loading)
- **test_characters_api.py** - API endpoints (health, characters, avatars)

---

## Energy Saving

Full container shutdown after 5 min inactivity:

```bash
# Add to crontab
* * * * * /opt/cathyAI/watchdog.sh
```

The watchdog script monitors `/tmp/last_activity` and shuts down containers when inactive.

---

## Development Workflow

1. Work on `dmz` branch:
   ```bash
   ./setup_git.sh
   git add .
   git commit -m "feat: ..."
   git push origin dmz
   ```

2. GitHub Actions runs tests automatically
3. On pass → auto-merge to `main`
4. Nightly auto-deploy:
   ```bash
   0 2 * * * cd /opt/cathyAI && git pull origin main && \
     cd webbui_chat && docker compose up -d --build && \
     cd ../characters_api && docker compose up -d --build
   ```

## Development Standards

See [.amazonq/rules/dev-standards.md](.amazonq/rules/dev-standards.md) for detailed development guidelines including:
- PEP 8 compliance and reST docstring standards
- Commit message format requirements
- Post-change documentation update requirements

---

## Tech Stack

- **Chat UI**: [Chainlit](https://github.com/Chainlit/chainlit)
- **API Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **HTTP Client**: [httpx](https://www.python-httpx.org/)
- **Testing**: pytest with class-based fixtures
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Deployment**: Proxmox LXC containers

---

## License

Personal hobby project — free to fork and modify
