# cathyAI

A customizable AI companion web app built with Chainlit, featuring multi-character support, live Ollama model switching, emotion detection, and energy-efficient GPU management.

## Features

- Multi-Character Support — JSON-based characters with avatars, greetings, and individual system prompts; switch via top-left profile dropdown
- Live Model Switching — Dropdown with all downloaded Ollama models (sidebar settings)
- Energy Efficient — Immediate model unload after responses + full container shutdown after 5 min inactivity
- Modern UI — Native Chainlit interface with profile avatars and responsive chat bubbles
- Docker Ready — Containerized with docker-compose
- CI/CD Pipeline — Automated testing + auto-merge/deploy via GitHub Actions

## Architecture

- Frontend/UI: Chainlit (native responsive chat with profiles)
- Backend: Python + Ollama for LLM inference
- Deployment: Docker
- LLM Server: Ollama

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

chainlit run app.py                 # Launch app

# Access at http://localhost:8000
```

### Docker Deployment (Proxmox CT 202)

```bash
docker compose up -d --build        # Run in background

# Rebuild on changes
docker compose up -d --build

# Stop
docker compose down
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

- Sidebar gear icon → "Ollama Model" dropdown lists all downloaded models.
- Changes apply immediately to current chat.

## Energy Saving

- Models unload instantly after each response (`keep_alive: 0`).
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
- App import & character loading logic

## Tech Stack

- **Framework**: [Chainlit](https://github.com/Chainlit/chainlit)
- **UI Components**: [LiftKit](https://github.com/Chainlift/liftkit)
- **LLM**: [Ollama](https://ollama.ai/) (llama3.1:8b)
- **Emotion Detection**: [DistilBERT](https://huggingface.co/bhadresh-savani/distilbert-base-uncased-emotion)
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Deployment**: Proxmox LXC containers

## License

Personal hobby project — free to fork and modify
