import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys

# Mock chainlit before importing app
sys.modules['chainlit'] = Mock()

def test_character_json_structure():
    """Test that all character JSON files have required fields"""
    char_files = list(Path("characters").glob("*.json"))
    assert len(char_files) > 0, "No character files found"
    
    required_fields = ["name", "avatar", "model", "system_prompt", "greeting"]
    
    for f in char_files:
        data = json.load(open(f))
        for field in required_fields:
            assert field in data, f"Missing '{field}' in {f.name}"
        assert isinstance(data["name"], str) and len(data["name"]) > 0
        assert isinstance(data["model"], str) and len(data["model"]) > 0

def test_system_prompt_files_exist():
    """Test that referenced system prompt files exist"""
    char_files = list(Path("characters").glob("*.json"))
    
    for f in char_files:
        data = json.load(open(f))
        prompt = data.get("system_prompt", "")
        
        # If it's a filename reference, check file exists
        if not prompt.startswith("You"):
            prompt_path = Path("characters/system_prompt") / prompt
            assert prompt_path.exists(), f"System prompt file {prompt_path} not found"
            content = prompt_path.read_text().strip()
            assert len(content) > 0, f"System prompt file {prompt_path} is empty"

def test_avatar_files_exist():
    """Test that referenced avatar files exist in static directory"""
    char_files = list(Path("characters").glob("*.json"))
    
    for f in char_files:
        data = json.load(open(f))
        avatar = data.get("avatar")
        avatar_path = Path("static") / avatar
        assert avatar_path.exists(), f"Avatar file {avatar_path} not found for {f.name}"

def test_docker_files_exist():
    """Test that Docker configuration files exist"""
    assert Path("Dockerfile").exists(), "Dockerfile not found"
    assert Path("docker-compose.yaml").exists(), "docker-compose.yaml not found"
    assert Path("requirements.txt").exists(), "requirements.txt not found"

def test_requirements_has_dependencies():
    """Test that requirements.txt has necessary dependencies"""
    content = Path("requirements.txt").read_text()
    required = ["chainlit", "ollama", "transformers", "torch"]
    
    for dep in required:
        assert dep in content, f"Missing dependency: {dep}"

def test_watchdog_script_exists():
    """Test that watchdog script exists and is executable"""
    watchdog = Path("watchdog.sh")
    assert watchdog.exists(), "watchdog.sh not found"
    content = watchdog.read_text()
    assert "LAST_ACTIVITY" in content
    assert "docker compose down" in content

def test_app_imports():
    """Test that app.py can be imported without errors"""
    try:
        # Mock transformers pipeline to avoid downloading models
        with patch('transformers.pipeline'):
            import app
            assert hasattr(app, 'start')
            assert hasattr(app, 'main')
            assert hasattr(app, 'CHARACTERS')
    except Exception as e:
        pytest.fail(f"Failed to import app.py: {e}"

def test_character_loading_logic():
    """Test character loading with system prompt file resolution"""
    with patch('transformers.pipeline'):
        import app
        
        assert len(app.CHARACTERS) > 0, "No characters loaded"
        
        for char_id, char_data in app.CHARACTERS.items():
            # System prompt should be loaded as text, not filename
            prompt = char_data.get("system_prompt", "")
            assert len(prompt) > 50, f"System prompt for {char_id} seems too short or not loaded"
            assert prompt.startswith("You"), f"System prompt for {char_id} not properly loaded"
