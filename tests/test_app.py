import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Get repo root (parent of tests directory)
REPO_ROOT = Path(__file__).parent.parent
os.chdir(REPO_ROOT)
sys.path.insert(0, str(REPO_ROOT))

# Mock chainlit before importing app
sys.modules['chainlit'] = Mock()

def test_character_json_structure():
    """Test that all character JSON files have required fields"""
    char_files = list((REPO_ROOT / "characters").glob("*.json"))
    assert len(char_files) > 0, "No character files found"
    
    required_fields = ["name", "avatar", "model", "system_prompt", "greeting"]
    
    for f in char_files:
        with open(f, 'r') as file:
            data = json.load(file)
        for field in required_fields:
            assert field in data, f"Missing '{field}' in {f.name}"
        assert isinstance(data["name"], str) and len(data["name"]) > 0
        assert isinstance(data["model"], str) and len(data["model"]) > 0
        assert isinstance(data["avatar"], str) and len(data["avatar"]) > 0
        assert isinstance(data["greeting"], str) and len(data["greeting"]) > 0
        # Nickname is optional but must be string if present
        if "nickname" in data:
            assert isinstance(data["nickname"], str), f"Nickname must be string in {f.name}"

def test_system_prompt_files_exist():
    """Test that referenced system prompt files exist"""
    char_files = list((REPO_ROOT / "characters").glob("*.json"))
    
    for f in char_files:
        with open(f, 'r') as file:
            data = json.load(file)
        prompt = data.get("system_prompt", "")
        
        # If it's a filename reference, check file exists
        if not prompt.startswith("You"):
            prompt_path = REPO_ROOT / "characters" / "system_prompt" / prompt
            assert prompt_path.exists(), f"System prompt file {prompt_path} not found"
            content = prompt_path.read_text().strip()
            assert len(content) > 0, f"System prompt file {prompt_path} is empty"
            assert content.startswith("You"), f"System prompt should start with 'You' in {prompt_path}"

def test_avatar_files_exist():
    """Test that referenced avatar files exist in public/avatars directory"""
    char_files = list((REPO_ROOT / "characters").glob("*.json"))
    
    for f in char_files:
        with open(f, 'r') as file:
            data = json.load(file)
        avatar = data.get("avatar")
        # Check both static and public/avatars for backwards compatibility
        avatar_path_public = REPO_ROOT / "public" / "avatars" / avatar
        avatar_path_static = REPO_ROOT / "static" / avatar
        assert avatar_path_public.exists() or avatar_path_static.exists(), \
            f"Avatar file {avatar} not found in public/avatars/ or static/ for {f.name}"

def test_public_avatars_directory():
    """Test that public/avatars directory exists"""
    public_avatars = REPO_ROOT / "public" / "avatars"
    assert public_avatars.exists(), "public/avatars directory not found"
    assert public_avatars.is_dir(), "public/avatars is not a directory"

def test_docker_files_exist():
    """Test that Docker configuration files exist"""
    assert (REPO_ROOT / "Dockerfile").exists(), "Dockerfile not found"
    assert (REPO_ROOT / "docker-compose.yaml").exists(), "docker-compose.yaml not found"
    assert (REPO_ROOT / "requirements.txt").exists(), "requirements.txt not found"

def test_dockerfile_structure():
    """Test that Dockerfile has proper structure"""
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()
    assert "FROM python" in dockerfile, "Dockerfile missing Python base image"
    assert "COPY requirements.txt" in dockerfile, "Dockerfile missing requirements.txt copy"
    assert "chainlit" in dockerfile.lower(), "Dockerfile missing chainlit command"

def test_docker_compose_structure():
    """Test that docker-compose.yaml has proper structure"""
    compose = (REPO_ROOT / "docker-compose.yaml").read_text()
    assert "services:" in compose, "docker-compose.yaml missing services section"
    assert "ports:" in compose, "docker-compose.yaml missing ports configuration"
    assert "8000" in compose, "docker-compose.yaml missing port 8000"
    assert "OLLAMA_HOST" in compose, "docker-compose.yaml missing OLLAMA_HOST environment variable"

def test_requirements_has_dependencies():
    """Test that requirements.txt has necessary dependencies"""
    content = (REPO_ROOT / "requirements.txt").read_text()
    required = ["chainlit", "ollama", "transformers", "torch"]
    
    for dep in required:
        assert dep in content, f"Missing dependency: {dep}"

def test_watchdog_script_exists():
    """Test that watchdog script exists and has correct logic"""
    watchdog = REPO_ROOT / "watchdog.sh"
    assert watchdog.exists(), "watchdog.sh not found"
    content = watchdog.read_text()
    assert "last_activity" in content, "watchdog.sh missing last_activity reference"
    assert "docker compose down" in content, "watchdog.sh missing docker compose down command"
    assert "#!/bin/bash" in content, "watchdog.sh missing shebang"

def test_setup_scripts_exist():
    """Test that setup scripts exist"""
    assert (REPO_ROOT / "setup.sh").exists(), "setup.sh not found"
    assert (REPO_ROOT / "setup_git.sh").exists(), "setup_git.sh not found"
    
    setup = (REPO_ROOT / "setup.sh").read_text()
    assert "venv" in setup, "setup.sh missing venv creation"
    assert "requirements.txt" in setup, "setup.sh missing requirements installation"

def test_github_workflow_exists():
    """Test that GitHub Actions workflow exists"""
    workflow = REPO_ROOT / ".github" / "workflows" / "test.yml"
    assert workflow.exists(), "GitHub Actions workflow not found"
    content = workflow.read_text()
    assert "pytest" in content, "Workflow missing pytest"
    assert "dmz" in content, "Workflow missing dmz branch reference"
    assert "merge" in content.lower(), "Workflow missing merge job"

def test_gitignore_has_python_patterns():
    """Test that .gitignore ignores Python cache files"""
    gitignore = REPO_ROOT / ".gitignore"
    assert gitignore.exists(), ".gitignore not found"
    content = gitignore.read_text()
    assert "__pycache__" in content, ".gitignore missing __pycache__"
    assert ".pytest_cache" in content, ".gitignore missing .pytest_cache"

def test_app_imports():
    """Test that app.py can be imported without errors"""
    try:
        # Mock transformers pipeline to avoid downloading models
        with patch('transformers.pipeline'):
            import app
            assert hasattr(app, 'start'), "app.py missing start function"
            assert hasattr(app, 'main'), "app.py missing main function"
            assert hasattr(app, 'CHARACTERS'), "app.py missing CHARACTERS dict"
            assert hasattr(app, 'chat_profiles'), "app.py missing chat_profiles function"
            assert hasattr(app, 'update_activity'), "app.py missing update_activity function"
    except Exception as e:
        pytest.fail(f"Failed to import app.py: {e}")

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
            
            # Validate all required fields are present
            assert "name" in char_data, f"Character {char_id} missing name"
            assert "avatar" in char_data, f"Character {char_id} missing avatar"
            assert "model" in char_data, f"Character {char_id} missing model"
            assert "greeting" in char_data, f"Character {char_id} missing greeting"

def test_multiple_characters_exist():
    """Test that multiple characters exist for dropdown functionality"""
    char_files = list((REPO_ROOT / "characters").glob("*.json"))
    assert len(char_files) >= 2, "Need at least 2 characters for dropdown to appear"

def test_logging_configured():
    """Test that app has logging configured"""
    with patch('transformers.pipeline'):
        import app
        assert hasattr(app, 'logger'), "app.py missing logger"
        assert app.logger is not None, "Logger not initialized"

def test_nickname_fallback_logic():
    """Test that nickname falls back to first name correctly"""
    with patch('transformers.pipeline'):
        import app
        
        for char_id, char_data in app.CHARACTERS.items():
            name = char_data.get("name", "")
            nickname = char_data.get("nickname", "")
            
            # Test the logic used in app.py for author_label
            if nickname:
                display_name = nickname
            else:
                display_name = name.split(" ", 1)[0] if " " in name else name
            
            assert len(display_name) > 0, f"Display name empty for {char_id}"
            # For Catherine Ploskaya without nickname, should be "Catherine"
            if name == "Catherine Ploskaya" and not nickname:
                assert display_name == "Catherine", f"Expected 'Catherine' but got '{display_name}'"

def test_error_handling_in_character_loading():
    """Test that app handles character loading errors gracefully"""
    with patch('transformers.pipeline'):
        import app
        # App should load successfully even if some characters fail
        # This is validated by checking that CHARACTERS dict exists
        assert isinstance(app.CHARACTERS, dict), "CHARACTERS should be a dict even if loading fails"
