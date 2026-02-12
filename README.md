# cathyAI

A customizable AI companion web app built with Chainlit, featuring multi-character support, live model switching via external APIs, optional emotion detection, and energy-efficient container management.

## Features

- Multi-Character Support — JSON-based characters with avatars, greetings, and individual system prompts; switch via top-left profile dropdown
- Live Model Switching — Dropdown with all available models from external API (sidebar settings)
- API-Based Architecture — Connects to external chat, model listing, and emotion detection APIs
- Energy Efficient — Full container shutdown after 5 min inactivity
- Modern UI — Native Chainlit interface with profile avatars and responsive chat bubbles
- Docker Ready — Containerized with docker-compose
- CI/CD Pipeline — Automated testing + auto-merge/deploy via GitHub Actions

## Architecture

- Frontend/UI: Chainlit (native responsive chat with profiles)
- Backend: Python + httpx for API communication
- LLM Server: External API (configurable via environment variables)
- Deployment: Docker

## Project Structure

```
cathyAI/
├── app.py                          # Main Chainlit application
├── characters/
│   ├── [character].json            # Character configuration
│   ├── system_prompt/              # External system prompt files
│   └── character_info/             # Optional character lore/backstory
├── public/
│   └── avatars/                    # Character avatar images (served automatically)
├── tests/
│   └── test_app.py                 # Comprehensive test suite
├── .github/workflows/
│   └── test.yml                    # CI/CD with Debian container tests + auto-merge
├── docker-compose.yaml             # Docker orchestration
├── Dockerfile                      # Container build
├── requirements.txt                # Python dependencies
├── .env.template                   # Environment variable template
├── watchdog.sh                     # Inactivity shutdown script
├── setup.sh                        # Local dev environment setup
├── setup_git.sh                    # Git branch setup helper
├── .gitignore                      # Ignores caches and venv
└── README.md                       # This file
```

## Setup

### Local Development

```bash
./setup.sh                          # Creates venv + installs deps

# Configure API endpoints
cp .env.template .env
# Edit .env with your API URLs

chainlit run app.py                 # Launch app

# Access at http://localhost:8000
```

### Docker Deployment (Proxmox CT 202)

```bash
# Configure environment
cp .env.template .env
# Edit .env with your API endpoints

docker compose up -d --build        # Run in background

# Rebuild on changes
docker compose up -d --build

# Stop
docker compose down
```

## Configuration

### Environment Variables (.env)

```bash
# Required: External API endpoints
CHAT_API_URL=http://your-api:11434/api/chat
MODELS_API_URL=http://your-api:11434/api/tags

# Optional: Emotion detection (disabled by default)
EMOTION_ENABLED=0
EMOTION_API_URL=http://your-api:8001/emotion

# Optional: API authentication
CHAT_API_KEY=your_key_here
MODELS_API_KEY=your_key_here
EMOTION_API_KEY=your_key_here

# Optional: Timeouts (seconds)
CHAT_TIMEOUT=120
MODELS_TIMEOUT=10
EMOTION_TIMEOUT=10
```

### API Requirements

**Models API (GET)** - Returns list of available models:
```json
{"models": ["modelA", "modelB"]}
```

**Chat API (POST)** - Streaming chat endpoint:
```json
// Request
{"model": "modelA", "messages": [{"role": "user", "content": "Hi"}], "stream": true}

// Response (SSE or NDJSON)
{"token": "Hello"}
// or non-streaming fallback
{"reply": "Hello there!"}
```

**Emotion API (POST)** - Optional emotion detection:
```json
// Request
{"text": "I am happy!"}

// Response
{"label": "joy", "score": 0.87}
```

## Character Configuration

Add JSON files in `characters/`:

```json
{
  "name": "Character name",
  "nickname": "[OPTIONAL] Nickname",             
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

- Avatars auto-show in profile dropdown and chat bubbles.
- Multiple characters → dropdown appears for switching (new isolated session each).

## Model Selection

- Sidebar gear icon → "Ollama Model" dropdown lists all models from MODELS_API_URL.
- Changes apply immediately to current chat.

## Energy Saving

- Full container shutdown after 5 min inactivity:

```bash
# Add to crontab
* * * * * /opt/cathyAI/watchdog.sh
```

## Development Workflow

1. Work on `dmz` branch:
   ```bash
   ./setup_git.sh
   git add .
   git commit -m "feat: ..."
   git push origin dmz
   ```

2. GitHub Actions tests run automatically.
3. On pass → auto-merge to `main`.
4. Nightly auto-deploy:
   ```bash
   0 2 * * * cd /opt/cathyAI && git pull origin main && docker compose up -d --build
   ```

## Testing

```bash
pytest

pytest tests/test_app.py -v

pytest tests/test_app.py::test_avatar_files_exist
```

Tests cover:
- JSON structure & required fields
- External system prompt files
- Avatar files in public/avatars/
- Docker/requirements/watchdog presence
- App import & API function existence
- Environment template configuration

## Tech Stack

- **Framework**: [Chainlit](https://github.com/Chainlit/chainlit)
- **UI Components**: [LiftKit](https://github.com/Chainlift/liftkit)
- **HTTP Client**: [httpx](https://www.python-httpx.org/)
- **External APIs**: Chat, Model Listing, Emotion Detection (configurable)
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Deployment**: Proxmox LXC containers

## License

Personal hobby project — free to fork and modify