"""Test suite for characters_api FastAPI service.

Tests character API endpoints, file resolution, and Docker configuration.
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
import sys
import os

REPO_ROOT = Path(__file__).parent.parent


class TestCharactersAPI:
    """Test suite for characters_api with isolated imports."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test to ensure clean imports."""
        # Setup
        original_path = sys.path.copy()
        original_modules = set(sys.modules.keys())
        
        os.chdir(REPO_ROOT)
        sys.path.insert(0, str(REPO_ROOT / "characters_api"))
        os.environ["CHAR_DIR"] = str(REPO_ROOT / "characters")
        os.environ["CHAR_API_KEY"] = ""
        
        from app import app, CHAR_DIR, PROMPT_DIR, INFO_DIR
        self.app = app
        self.client = TestClient(app)
        self.CHAR_DIR = CHAR_DIR
        self.PROMPT_DIR = PROMPT_DIR
        self.INFO_DIR = INFO_DIR
        
        yield
        
        # Teardown
        sys.path = original_path
        new_modules = set(sys.modules.keys()) - original_modules
        for mod in new_modules:
            if mod.startswith('app'):
                sys.modules.pop(mod, None)

    def test_health_endpoint(self):
        """Test health check endpoint returns ok status."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "char_dir" in data

    def test_list_characters(self):
        """Test listing all characters."""
        response = self.client.get("/characters")
        assert response.status_code == 200
        data = response.json()
        assert "characters" in data
        assert len(data["characters"]) > 0
        
        for char in data["characters"]:
            assert "id" in char
            assert "name" in char
            assert "model" in char
            assert "aliases" in char
            assert isinstance(char["aliases"], list)

    def test_get_character_by_id(self):
        """Test retrieving specific character by ID."""
        response = self.client.get("/characters/catherine")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Catherine Ploskaya"
        assert "system_prompt" in data
        assert len(data["system_prompt"]) > 50
        assert "aliases" in data
        assert "catherine" in [a.lower() for a in data["aliases"]]

    def test_get_nonexistent_character(self):
        """Test 404 response for nonexistent character."""
        response = self.client.get("/characters/nonexistent")
        assert response.status_code == 404

    def test_system_prompt_resolution(self):
        """Test that system prompts are resolved from files."""
        response = self.client.get("/characters/catherine")
        assert response.status_code == 200
        data = response.json()
        prompt = data["system_prompt"]
        assert prompt.startswith("You")
        assert len(prompt) > 100

    def test_character_aliases(self):
        """Test that character aliases are built correctly."""
        response = self.client.get("/characters/catherine")
        assert response.status_code == 200
        data = response.json()
        aliases = [a.lower() for a in data["aliases"]]
        assert "catherine" in aliases
        assert "catherine ploskaya" in aliases

    def test_docker_files_exist(self):
        """Test that Docker configuration files exist."""
        api_dir = REPO_ROOT / "characters_api"
        assert (api_dir / "Dockerfile").exists(), "characters_api/Dockerfile not found"
        assert (api_dir / "docker-compose.yaml").exists(), "characters_api/docker-compose.yaml not found"
        assert (api_dir / "requirements.txt").exists(), "characters_api/requirements.txt not found"

    def test_dockerfile_structure(self):
        """Test that Dockerfile has proper structure."""
        dockerfile = (REPO_ROOT / "characters_api" / "Dockerfile").read_text()
        assert "FROM python" in dockerfile, "Dockerfile missing Python base image"
        assert "uvicorn" in dockerfile, "Dockerfile missing uvicorn command"
        assert "8090" in dockerfile, "Dockerfile missing port 8090"

    def test_docker_compose_structure(self):
        """Test that docker-compose.yaml has proper structure."""
        compose = (REPO_ROOT / "characters_api" / "docker-compose.yaml").read_text()
        assert "characters_api:" in compose, "docker-compose.yaml missing characters_api service"
        assert "8090:8090" in compose, "docker-compose.yaml missing port 8090"
        assert "../characters" in compose, "docker-compose.yaml missing characters volume"
        assert "../public" in compose, "docker-compose.yaml missing public volume"

    def test_requirements_has_dependencies(self):
        """Test that requirements.txt has necessary dependencies."""
        content = (REPO_ROOT / "characters_api" / "requirements.txt").read_text()
        assert "fastapi" in content, "Missing dependency: fastapi"
        assert "uvicorn" in content, "Missing dependency: uvicorn"

    def test_env_template_exists(self):
        """Test that .env.template exists with required variables."""
        env_template = REPO_ROOT / "characters_api" / ".env.template"
        assert env_template.exists(), "characters_api/.env.template not found"
        content = env_template.read_text()
        assert "CHAR_API_KEY" in content, ".env.template missing CHAR_API_KEY"
        assert "HOST_URL" in content, ".env.template missing HOST_URL"

    def test_app_structure(self):
        """Test that app.py has correct structure."""
        app_file = REPO_ROOT / "characters_api" / "app.py"
        content = app_file.read_text()
        assert "FastAPI" in content, "app.py missing FastAPI import"
        assert "def health" in content, "app.py missing health function"
        assert "def list_characters" in content, "app.py missing list_characters function"
        assert "def get_character" in content, "app.py missing get_character function"
