"""Test suite for cathyAI core application.

Tests application structure, dependencies, and configuration.
"""

import pytest
import json
from pathlib import Path
import sys
import os

# Get repo root
REPO_ROOT = Path(__file__).parent.parent
os.chdir(REPO_ROOT)


class TestAppStructure:
    """Test suite for cathyAI application structure."""

    def test_main_app_exists(self):
        """Test that main application file exists."""
        assert (REPO_ROOT / "app.py").exists(), "app.py not found"
        assert (REPO_ROOT / "auth_api.py").exists(), "auth_api.py not found"
        assert (REPO_ROOT / "users.py").exists(), "users.py not found"

    def test_docker_files_exist(self):
        """Test that Docker configuration files exist."""
        assert (REPO_ROOT / "Dockerfile").exists(), "Dockerfile not found"
        assert (REPO_ROOT / "docker-compose.yaml").exists(), "docker-compose.yaml not found"
        assert (REPO_ROOT / "requirements.txt").exists(), "requirements.txt not found"

    def test_env_template_exists(self):
        """Test that .env.template exists with required variables."""
        env_template = REPO_ROOT / ".env.template"
        assert env_template.exists(), ".env.template not found"
        content = env_template.read_text()
        
        # Required API endpoints
        assert "CHAT_API_URL=" in content, ".env.template missing CHAT_API_URL"
        assert "MODELS_API_URL=" in content, ".env.template missing MODELS_API_URL"
        assert "CHAR_API_URL=" in content, ".env.template missing CHAR_API_URL"
        assert "CHAR_API_KEY=" in content, ".env.template missing CHAR_API_KEY"
        
        # Authentication
        assert "CHAINLIT_AUTH_SECRET=" in content, ".env.template missing CHAINLIT_AUTH_SECRET"
        assert "USER_DB_PATH=" in content, ".env.template missing USER_DB_PATH"
        assert "USER_ADMIN_API_KEY=" in content, ".env.template missing USER_ADMIN_API_KEY"
        assert "REGISTRATION_ENABLED=" in content, ".env.template missing REGISTRATION_ENABLED"
        assert "REGISTRATION_REQUIRE_INVITE=" in content, ".env.template missing REGISTRATION_REQUIRE_INVITE"

    def test_requirements_has_dependencies(self):
        """Test that requirements.txt has necessary dependencies."""
        content = (REPO_ROOT / "requirements.txt").read_text()
        required = ["chainlit", "httpx", "python-dotenv", "fastapi", "uvicorn", "passlib", "bcrypt"]
        
        for dep in required:
            assert dep in content, f"Missing dependency: {dep}"

    def test_docker_compose_structure(self):
        """Test that docker-compose.yaml has proper structure."""
        compose = (REPO_ROOT / "docker-compose.yaml").read_text()
        assert "webbui_chat:" in compose, "docker-compose.yaml missing webbui_chat service"
        assert "webbui_auth_api:" in compose, "docker-compose.yaml missing webbui_auth_api service"
        assert "8000:8000" in compose, "docker-compose.yaml missing port 8000"
        assert "8001:8001" in compose, "docker-compose.yaml missing port 8001"
        assert "./state:/state" in compose, "docker-compose.yaml missing state volume"

    def test_setup_scripts_exist(self):
        """Test that setup scripts exist."""
        assert (REPO_ROOT / "setup.sh").exists(), "setup.sh not found"
        assert (REPO_ROOT / "setup_git.sh").exists(), "setup_git.sh not found"
        assert (REPO_ROOT / "generate_secrets.py").exists(), "generate_secrets.py not found"
        assert (REPO_ROOT / "bootstrap_admin.py").exists(), "bootstrap_admin.py not found"

    def test_github_workflow_exists(self):
        """Test that GitHub Actions workflow exists."""
        workflow = REPO_ROOT / ".github" / "workflows" / "test.yml"
        assert workflow.exists(), "GitHub Actions workflow not found"
        content = workflow.read_text()
        assert "pytest" in content, "Workflow missing pytest"
        assert "dmz" in content, "Workflow missing dmz branch reference"
        assert "merge" in content.lower(), "Workflow missing merge job"

    def test_gitignore_has_python_patterns(self):
        """Test that .gitignore ignores Python cache files."""
        gitignore = REPO_ROOT / ".gitignore"
        assert gitignore.exists(), ".gitignore not found"
        content = gitignore.read_text()
        assert "__pycache__" in content, ".gitignore missing __pycache__"
        assert ".pytest_cache" in content, ".gitignore missing .pytest_cache"
        assert ".env" in content, ".gitignore missing .env"

    def test_user_management_docs_exist(self):
        """Test that user management documentation exists."""
        assert (REPO_ROOT / "USER_MANAGEMENT.md").exists(), "USER_MANAGEMENT.md not found"

    def test_chainlit_config_exists(self):
        """Test that Chainlit configuration exists."""
        assert (REPO_ROOT / ".chainlit" / "config.toml").exists(), "Chainlit config.toml not found"
        assert (REPO_ROOT / "chainlit.md").exists(), "chainlit.md not found"