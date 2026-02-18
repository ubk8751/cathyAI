"""Test suite for webbui_chat Chainlit application.

Tests chat UI, character loading, and Docker configuration.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock
import sys
import os

REPO_ROOT = Path(__file__).parent.parent


class TestWebbuiChat:
    """Test suite for webbui_chat with isolated imports."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, monkeypatch):
        """Setup and teardown for each test to ensure clean imports."""
        # Setup
        original_path = sys.path.copy()
        original_modules = set(sys.modules.keys())
        
        os.chdir(REPO_ROOT)
        
        # Mock Path to return correct character directory
        original_cwd = os.getcwd()
        monkeypatch.chdir(REPO_ROOT / "webbui_chat")
        
        sys.path.insert(0, str(REPO_ROOT / "webbui_chat"))
        sys.modules['chainlit'] = Mock()
        
        import app
        self.app = app
        
        yield
        
        # Teardown
        monkeypatch.chdir(original_cwd)
        sys.path = original_path
        new_modules = set(sys.modules.keys()) - original_modules
        for mod in new_modules:
            if mod.startswith('app') or mod == 'chainlit':
                sys.modules.pop(mod, None)

    def test_docker_files_exist(self):
        """Test that Docker configuration files exist."""
        chat_dir = REPO_ROOT / "webbui_chat"
        assert (chat_dir / "Dockerfile").exists(), "webbui_chat/Dockerfile not found"
        assert (chat_dir / "docker-compose.yaml").exists(), "webbui_chat/docker-compose.yaml not found"
        assert (chat_dir / "requirements.txt").exists(), "webbui_chat/requirements.txt not found"

    def test_dockerfile_structure(self):
        """Test that Dockerfile has proper structure."""
        dockerfile = (REPO_ROOT / "webbui_chat" / "Dockerfile").read_text()
        assert "FROM python" in dockerfile, "Dockerfile missing Python base image"
        assert "chainlit" in dockerfile.lower(), "Dockerfile missing chainlit command"
        assert "8000" in dockerfile, "Dockerfile missing port 8000"

    def test_docker_compose_structure(self):
        """Test that docker-compose.yaml has proper structure."""
        compose = (REPO_ROOT / "webbui_chat" / "docker-compose.yaml").read_text()
        assert "webbui_chat:" in compose, "docker-compose.yaml missing webbui_chat service"
        assert "8000:8000" in compose, "docker-compose.yaml missing port 8000"
        assert "../characters:/app/characters" in compose, "docker-compose.yaml missing characters volume"
        assert "../public:/app/public" in compose, "docker-compose.yaml missing public volume"

    def test_requirements_has_dependencies(self):
        """Test that requirements.txt has necessary dependencies."""
        content = (REPO_ROOT / "webbui_chat" / "requirements.txt").read_text()
        required = ["chainlit", "httpx", "python-dotenv"]
        
        for dep in required:
            assert dep in content, f"Missing dependency: {dep}"
        
        assert "ollama" not in content, "ollama should be removed"
        assert "transformers" not in content, "transformers should be removed"

    def test_env_template_exists(self):
        """Test that .env.template exists with required variables."""
        env_template = REPO_ROOT / ".env.template"
        assert env_template.exists(), ".env.template not found"
        content = env_template.read_text()
        assert "CHAT_API_URL" in content, ".env.template missing CHAT_API_URL"
        assert "MODELS_API_URL" in content, ".env.template missing MODELS_API_URL"

    def test_app_imports(self):
        """Test that app.py can be imported without errors."""
        assert hasattr(self.app, 'start'), "app.py missing start function"
        assert hasattr(self.app, 'main'), "app.py missing main function"
        assert hasattr(self.app, 'update_settings'), "app.py missing update_settings function"
        assert hasattr(self.app, 'CHAR_LIST'), "app.py missing CHAR_LIST"
        assert hasattr(self.app, 'CHAR_INDEX'), "app.py missing CHAR_INDEX"
        assert hasattr(self.app, 'CHAR_LIST_ETAG'), "app.py missing CHAR_LIST_ETAG"
        assert hasattr(self.app, 'CHAR_PRIVATE_ETAGS'), "app.py missing CHAR_PRIVATE_ETAGS"
        assert hasattr(self.app, 'PROFILE_NAME_TO_ID'), "app.py missing PROFILE_NAME_TO_ID"
        assert hasattr(self.app, 'chat_profiles'), "app.py missing chat_profiles function"
        assert hasattr(self.app, 'update_activity'), "app.py missing update_activity function"
        assert hasattr(self.app, 'fetch_models'), "app.py missing fetch_models function"
        assert hasattr(self.app, 'stream_chat'), "app.py missing stream_chat function"
        assert hasattr(self.app, 'detect_emotion'), "app.py missing detect_emotion function"
        assert hasattr(self.app, 'fetch_characters_list'), "app.py missing fetch_characters_list function"
        assert hasattr(self.app, 'fetch_character_private'), "app.py missing fetch_character_private function"

    def test_character_loading_logic(self):
        """Test character API integration functions exist."""
        import inspect
        
        assert callable(self.app.fetch_characters_list), "fetch_characters_list should be callable"
        assert callable(self.app.fetch_character_private), "fetch_character_private should be callable"
        assert callable(self.app.load_cached_characters), "load_cached_characters should be callable"
        
        assert inspect.iscoroutinefunction(self.app.fetch_characters_list), "fetch_characters_list should be async"
        assert inspect.iscoroutinefunction(self.app.fetch_character_private), "fetch_character_private should be async"

    def test_logging_configured(self):
        """Test that app has logging configured."""
        assert hasattr(self.app, 'logger'), "app.py missing logger"
        assert self.app.logger is not None, "Logger not initialized"

    def test_nickname_fallback_logic(self):
        """Test that cache path is configured."""
        assert hasattr(self.app, 'CHAR_CACHE_PATH'), "app.py missing CHAR_CACHE_PATH"
        assert self.app.CHAR_CACHE_PATH is not None, "CHAR_CACHE_PATH not initialized"

    def test_api_functions_exist(self):
        """Test that API integration functions exist."""
        import inspect
        
        assert callable(self.app.fetch_models), "fetch_models should be callable"
        assert callable(self.app.stream_chat), "stream_chat should be callable"
        assert callable(self.app.detect_emotion), "detect_emotion should be callable"
        
        assert inspect.iscoroutinefunction(self.app.fetch_models), "fetch_models should be async"
        assert inspect.isasyncgenfunction(self.app.stream_chat), "stream_chat should be async generator"
        assert inspect.iscoroutinefunction(self.app.detect_emotion), "detect_emotion should be async"
