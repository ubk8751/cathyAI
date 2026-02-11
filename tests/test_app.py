import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import os

# Get repo root (parent of tests directory)
REPO_ROOT = Path(__file__).parent.parent
os.chdir(REPO_ROOT)
sys.path.insert(0, str(REPO_ROOT))

# Mock chainlit before importing app (prevents decorator issues)
sys.modules['chainlit'] = Mock()

def test_character_json_structure():
    """Test that all character JSON files have required fields"""
    char_files = list((REPO_ROOT / "characters").glob("*.json"))
    assert len(char_files) > 0, "No character files found"
    
    # "model" is now optional (fallback in code), but keep check for explicit if present
    required_fields = ["name", "avatar", "greeting", "system_prompt"]
    optional_fields = ["model", "nickname", "description"]
    
    for f in char_files:
        data = json.load(open(f))
        for field in required_fields:
            assert field in data, f"Missing required '{field}' in {f.name}"
        for field in optional_fields:
            if field in data:
                assert isinstance(data[field], str), f"Field '{field}' in {f.name} must be string"
        assert isinstance(data["name"], str) and len(data["name"].strip()) > 0
        assert isinstance(data["greeting"], str) and len(data["greeting"].strip()) > 0

def test_system_prompt_files_exist():
    """Test that referenced external system prompt files exist and have content"""
    char_files = list((REPO_ROOT / "characters").glob("*.json"))
    
    for f in char_files:
        data = json.load(open(f))
        prompt_ref = data.get("system_prompt", "")
        
        # If it's a filename reference (does not start with "You" – inline prompts do)
        if not prompt_ref.startswith("You"):
            prompt_path = REPO_ROOT / "characters" / "system_prompt" / prompt_ref
            assert prompt_path.exists(), f"Referenced system prompt file {prompt_path} not found for {f.name}"
            content = prompt_path.read_text().strip()
            assert len(content) > 0, f"System prompt file {prompt_path} is empty"

def test_avatar_files_exist():
    """Test that referenced avatar files exist in public/avatars/"""
    char_files = list((REPO_ROOT / "characters").glob("*.json"))
    
    avatars_dir = REPO_ROOT / "public" / "avatars"
    assert avatars_dir.exists(), "public/avatars/ directory not found"
    
    for f in char_files:
        data = json.load(open(f))
        avatar_filename = data.get("avatar")
        assert avatar_filename, f"No avatar specified in {f.name}"
        avatar_path = avatars_dir / avatar_filename
        assert avatar_path.exists(), f"Avatar file {avatar_path} not found for {f.name}"

def test_public_directory_structure():
    """Test that public/ and public/avatars/ directories exist"""
    public_dir = REPO_ROOT / "public"
    avatars_dir = public_dir / "avatars"
    assert public_dir.exists() and public_dir.is_dir(), "public/ directory missing"
    assert avatars_dir.exists() and avatars_dir.is_dir(), "public/avatars/ directory missing"

def test_docker_files_exist():
    """Test that Docker configuration files exist"""
    assert (REPO_ROOT / "Dockerfile").exists(), "Dockerfile not found"
    assert (REPO_ROOT / "docker-compose.yaml").exists(), "docker-compose.yaml not found"
    assert (REPO_ROOT / "requirements.txt").exists(), "requirements.txt not found"

def test_requirements_has_dependencies():
    """Test that requirements.txt has necessary dependencies"""
    content = (REPO_ROOT / "requirements.txt").read_text()
    required = ["chainlit", "ollama", "transformers", "torch"]
    
    for dep in required:
        assert dep in content.lower(), f"Missing dependency: {dep}"

def test_watchdog_script_exists():
    """Test that watchdog script exists and has core logic"""
    watchdog = REPO_ROOT / "watchdog.sh"
    assert watchdog.exists(), "watchdog.sh not found"
    content = watchdog.read_text()
    assert "/tmp/last_activity" in content or "last_activity" in content
    assert "docker" in content and ("stop" in content or "down" in content)

def test_app_imports():
    """Test that app.py can be imported without errors"""
    try:
        # Mock transformers pipeline to avoid model download attempts
        with patch('transformers.pipeline'), \
             patch('ollama.list'), \
             patch('ollama.chat'):
            import app
            # Check key attributes/decorators exist
            assert hasattr(app, 'chat_profiles') or hasattr(app, 'set_chat_profiles'), "Missing chat profiles setup"
            assert hasattr(app, 'on_chat_start') or hasattr(app, 'start')
            assert hasattr(app, 'on_message') or hasattr(app, 'main')
            assert hasattr(app, 'CHARACTERS')
    except Exception as e:
        pytest.fail(f"Failed to import app.py: {str(e)}")

def test_character_loading_logic():
    """Test character loading resolves external prompts and loads avatars correctly"""
    with patch('transformers.pipeline'), \
         patch('ollama.list'), \
         patch('ollama.chat'):
        import app
        
        assert len(app.CHARACTERS) > 0, "No characters loaded"
        
        for char_id, char_data in app.CHARACTERS.items():
            # System prompt should be full text (long, starts with "You")
            prompt = char_data.get("system_prompt", "")
            assert len(prompt) > 50, f"System prompt for {char_id} too short or not loaded"
            assert prompt.strip().startswith("You"), f"System prompt for {char_id} not properly resolved (should start with 'You')"
            
            # Avatar filename present
            assert "avatar" in char_data and char_data["avatar"], f"Missing avatar for {char_id}"
            
            # Greeting present
            assert "greeting" in char_data and char_data["greeting"], f"Missing greeting for {char_id}"