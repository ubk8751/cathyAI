# cathyAI

A customizable AI companion web app built with Chainlit, featuring emotion detection, dynamic character loading, and energy-efficient GPU management.

## Features

- 🐾 **Dynamic Character System** - JSON-based character definitions with custom avatars and system prompts
- 😺 **Emotion Detection** - Real-time emotion analysis using DistilBERT
- ⚡ **Energy Efficient** - Automatic GPU unload after responses and inactivity shutdown
- 🎨 **Modern UI** - Built with [Chainlit](https://github.com/Chainlit/chainlit) and styled with [LiftKit](https://github.com/Chainlift/liftkit)
- 🐳 **Docker Ready** - Containerized deployment with docker-compose
- 🔄 **CI/CD Pipeline** - Automated testing and deployment via GitHub Actions

## Architecture

- **Frontend**: Chainlit + LiftKit UI components
- **Backend**: Python with Ollama for LLM inference
- **Deployment**: Docker containers on Proxmox LXC
- **LLM Server**: Ollama (CT 203) with Vulkan GPU acceleration
- **App Server**: Docker (CT 202)

## Project Structure

```
cathyAI/
├── app.py                      # Main Chainlit application
├── characters/
│   ├── [character].json        # Character configuration
│   ├── system_prompt/          # Character system prompts
│   └── character_info/         # Character background info
├── static/                     # Avatar images
├── docker-compose.yaml         # Docker orchestration
├── Dockerfile                  # Container definition
├── requirements.txt            # Python dependencies
├── watchdog.sh                 # Inactivity shutdown script
├── test_app.py                 # Test suite
└── .github/workflows/test.yml  # CI/CD pipeline
```

## Setup

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
chainlit run app.py

# Access at http://localhost:8000
```

### Docker Deployment

```bash
# Build and run
docker compose up --build

# Run in background
docker compose up -d --build

# Stop
docker compose down
```

### Environment Variables

- `OLLAMA_HOST`: Ollama server URL (default: `http://192.168.1.57:11434`)

## Character Configuration

Create JSON files in `characters/` directory:

```json
{
  "name": "Character Name",
  "avatar": "avatar.jpg",
  "model": "llama3.1:8b",
  "system_prompt": "prompt_file.prompt",
  "greeting": "Hello!"
}
```

System prompts can be:
- Inline text starting with "You"
- Filename referencing `characters/system_prompt/*.prompt`

## Energy Saving

Automatic shutdown after 5 minutes of inactivity:

```bash
# Add to crontab
* * * * * /path/to/cathyAI/watchdog.sh
```

Ollama models unload immediately after each response (`keep_alive: 0`).

## Development Workflow

1. **Work on `dmz` branch**:
   ```bash
   git checkout dmz
   git add .
   git commit -m "your changes"
   git push
   ```

2. **Automated testing** runs on push to `dmz`

3. **Auto-merge to `main`** if tests pass

4. **Auto-deploy** via cron job:
   ```bash
   0 2 * * * cd /opt/cathyAI && git pull origin main && docker compose up -d --build
   ```

## Testing

```bash
# Run test suite
pytest

# Run specific test
pytest test_app.py::test_character_json_structure
```

Tests validate:
- Character JSON structure
- System prompt files
- Avatar files
- Docker configuration
- Dependencies
- App imports and logic

## Tech Stack

- **Framework**: [Chainlit](https://github.com/Chainlit/chainlit)
- **UI Components**: [LiftKit](https://github.com/Chainlift/liftkit)
- **LLM**: [Ollama](https://ollama.ai/) (llama3.1:8b)
- **Emotion Detection**: [DistilBERT](https://huggingface.co/bhadresh-savani/distilbert-base-uncased-emotion)
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Deployment**: Proxmox LXC containers

## License

Hobby project - use freely 🐾