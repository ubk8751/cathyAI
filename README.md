# cathyAI

A unified AI companion platform with Chainlit web UI, FastAPI authentication service, and external character API integration. Features multi-character support, live model switching, user authentication, and ETag-based caching.

## Overview

cathyAI is a single-service application with two components:

- **Chainlit Chat UI** - Main chat interface (port 8000)
- **Auth API** - FastAPI user management service (port 8001)

The application fetches character data from an external character API with ETag-based caching for bandwidth efficiency.

## Features

- **Multi-Character Support** - Fetches character profiles from external API with local caching
- **User Authentication** - SQLite-based password authentication with bcrypt hashing
- **User Management** - Registration with invite codes, admin controls, role-based access
- **Identity Resolution** - Dynamic user identity mapping via external identity API
- **Session Logging** - Persistent NDJSON conversation logs for memory/RAG foundation
- **Live Model Switching** - Dynamic model selection via external API
- **ETag Caching** - Efficient bandwidth usage with HTTP 304 responses
- **API-Based Architecture** - External chat, model listing, character data, and emotion detection APIs
- **Docker Ready** - Single docker-compose configuration with two containers
- **CI/CD Pipeline** - Automated testing with GitHub Actions

## Project Structure

```
cathyAI/
├── app.py                          # Main Chainlit application
├── auth_api.py                     # FastAPI user management service
├── users.py                        # User database operations
├── bootstrap_admin.py              # Admin account creation script
├── generate_secrets.py             # Secret key generation utility
├── Dockerfile                      # Container image definition
├── docker-compose.yaml             # Multi-container orchestration
├── requirements.txt                # Python dependencies
├── .env.template                   # Environment variable template
├── .env                            # Local configuration (gitignored)
├── chainlit.md                     # Chat UI welcome message
├── .chainlit/                      # Chainlit configuration
│   └── config.toml                 # UI settings
├── tests/                          # Test suites
│   ├── test_app.py                 # Core application tests
│   ├── test_auth.py                # Authentication tests
│   ├── test_webbui_chat.py         # Chat UI tests
│   └── test_characters_api.py      # External API integration tests
├── .github/workflows/test.yml      # CI/CD pipeline
├── setup_git.sh                    # Git workflow setup script
└── USER_MANAGEMENT.md              # Authentication documentation
```

## External Character API

The application expects an external character API (see [characters_api](https://github.com/ubk8751/cathyAI-character-api) for reference implementation) that provides:

- `GET /characters` - List all characters with public metadata
- `GET /characters/{id}?view=private` - Full character data with resolved prompts
- `GET /avatars/{filename}` - Avatar image serving

Characters are cached locally with ETag support for efficient bandwidth usage.

---

## Application Setup

### Setup

```bash
# Configure environment
cp .env.template .env
# Edit .env with your API endpoints and secrets

# Generate secrets
python generate_secrets.py

# Create admin account
python bootstrap_admin.py

# Docker (recommended)
docker compose up -d --build

# Local development
pip install -r requirements.txt
chainlit run app.py  # Chat UI on port 8000
python auth_api.py   # Auth API on port 8001
```

Access chat UI at http://localhost:8000

### Environment Variables

```bash
# Required: External API endpoints
CHAT_API_URL=http://your-api:8081/api/chat
MODELS_API_URL=http://your-api:8081/models

# Required: Character API
CHAR_API_URL=http://your-api:8090
CHAR_API_KEY=your_key_here

# Required: Identity API (for personalized user names)
IDENTITY_API_URL=http://your-api:8092
IDENTITY_API_KEY=your_key_here

# Required: Chainlit authentication
CHAINLIT_AUTH_SECRET=<generate with generate_secrets.py>

# User management
USER_DB_PATH=/state/users.sqlite
REGISTRATION_ENABLED=1
REGISTRATION_REQUIRE_INVITE=1
USER_ADMIN_API_KEY=<generate with generate_secrets.py>

# Optional: Emotion detection (disabled by default)
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

# Optional: State directory (default: /state)
STATE_DIR=/state
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

**Identity API (GET)** - Optional user identity resolution:
```json
// Request: GET /identity/resolve?external_id=chainlit:username:alice
// Headers: x-api-key: your_key

// Response
{"person_id": "p_alice", "preferred_name": "Alice"}
```

### Features

- **Character Profiles** - Dropdown with avatars loaded from external API
- **User Authentication** - SQLite-based password authentication with bcrypt
- **User Management** - Registration with invite codes, admin API for user control
- **Identity Resolution** - Optional personalized names via external identity API
- **Session Logging** - Persistent NDJSON logs in `/state/sessions/` for memory/RAG
- **Live Model Switching** - Sidebar dropdown for model selection
- **Streaming Chat** - Delta-based parser prevents duplicate text
- **ETag Caching** - Efficient character data caching with HTTP 304 responses
- **Optional Emotion Detection** - Configurable emotion analysis
- **Session History** - Per-user conversation tracking
- **Offline Resilience** - Local character cache fallback
- **Debug Commands** - `/whoami` for identity verification

See [USER_MANAGEMENT.md](USER_MANAGEMENT.md) for authentication setup.

---

## User Management

### Admin Operations

The auth API (port 8001) provides admin endpoints:

**POST /auth/register** - User registration (requires invite if enabled)
```bash
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass","invite_code":"code"}'
```

**POST /auth/admin/invite** - Create invite code
```bash
curl -X POST http://localhost:8001/auth/admin/invite \
  -H "x-admin-key: YOUR_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"expires_hours":24}'
```

**GET /auth/admin/users** - List all users
```bash
curl http://localhost:8001/auth/admin/users \
  -H "x-admin-key: YOUR_ADMIN_KEY"
```

**POST /auth/admin/disable** - Disable user
```bash
curl -X POST http://localhost:8001/auth/admin/disable \
  -H "x-admin-key: YOUR_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"username":"user"}'
```

**POST /auth/admin/enable** - Re-enable user
```bash
curl -X POST http://localhost:8001/auth/admin/enable \
  -H "x-admin-key: YOUR_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"username":"user"}'
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_app.py -v
pytest tests/test_auth.py -v

# Run specific test
pytest tests/test_app.py::TestAppStructure::test_main_app_exists
```

Test coverage:
- **test_app.py** (10 tests) - Application structure and dependencies
- **test_auth.py** (22 tests) - User authentication, registration, invite codes, admin operations
- **test_webbui_chat.py** (7 tests) - Chat UI Docker configuration and imports

---

## Development Workflow

1. Work on `dmz` branch:
   ```bash
   ./setup_git.sh
   git add .
   git commit -m "feat: ..."
   git push
   ```

2. GitHub Actions runs tests automatically (excludes auth tests)
3. On pass → auto-merge to `main`
4. Nightly auto-deploy:
   ```bash
   0 2 * * * cd /opt/cathyAI && git pull origin main && \
     docker compose up -d --build
   ```

## Docker Deployment

The docker-compose.yaml defines two services:

- **webbui_chat** - Main Chainlit application (port 8000)
- **webbui_auth_api** - FastAPI auth service (port 8001)

Both share the `/state` volume for SQLite database persistence.

```bash
# Build and start
docker compose up -d --build

# View logs
docker compose logs -f

# Stop services
docker compose down
```

---

## Tech Stack

- **Chat UI**: [Chainlit](https://github.com/Chainlit/chainlit)
- **Auth API**: [FastAPI](https://fastapi.tiangolo.com/)
- **HTTP Client**: [httpx](https://www.python-httpx.org/)
- **Password Hashing**: [passlib](https://passlib.readthedocs.io/) + [bcrypt](https://github.com/pyca/bcrypt/)
- **Database**: SQLite3
- **Testing**: pytest with class-based fixtures
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Deployment**: Proxmox LXC containers

---

## License

Personal hobby project — free to fork and modify
