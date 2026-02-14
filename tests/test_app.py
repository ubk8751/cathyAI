"""Test suite for cathyAI shared resources.

Tests character configuration files, avatars, and project structure.
"""

import pytest
import json
from pathlib import Path
import sys
import os

# Get repo root
REPO_ROOT = Path(__file__).parent.parent
os.chdir(REPO_ROOT)


class TestSharedResources:
    """Test suite for cathyAI shared resources and project structure."""

    def test_character_json_structure(self):
        """Test that all character JSON files have required fields.
        
        Validates presence and types of required fields in character configuration files.
        """
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
            if "nickname" in data:
                assert isinstance(data["nickname"], str), f"Nickname must be string in {f.name}"

    def test_system_prompt_files_exist(self):
        """Test that referenced system prompt files exist.
        
        Verifies external system prompt files are present and properly formatted.
        """
        char_files = list((REPO_ROOT / "characters").glob("*.json"))
        
        for f in char_files:
            with open(f, 'r') as file:
                data = json.load(file)
            prompt = data.get("system_prompt", "")
            
            if not prompt.startswith("You"):
                prompt_path = REPO_ROOT / "characters" / "system_prompt" / prompt
                assert prompt_path.exists(), f"System prompt file {prompt_path} not found"
                content = prompt_path.read_text().strip()
                assert len(content) > 0, f"System prompt file {prompt_path} is empty"
                assert content.startswith("You"), f"System prompt should start with 'You' in {prompt_path}"

    def test_avatar_files_exist(self):
        """Test that referenced avatar files exist in public/avatars directory.
        
        Checks for avatar file presence in both public/avatars and static directories.
        """
        char_files = list((REPO_ROOT / "characters").glob("*.json"))
        
        for f in char_files:
            with open(f, 'r') as file:
                data = json.load(file)
            avatar = data.get("avatar")
            avatar_path_public = REPO_ROOT / "public" / "avatars" / avatar
            avatar_path_static = REPO_ROOT / "static" / avatar
            assert avatar_path_public.exists() or avatar_path_static.exists(), \
                f"Avatar file {avatar} not found in public/avatars/ or static/ for {f.name}"

    def test_public_avatars_directory(self):
        """Test that public/avatars directory exists.
        
        :raises AssertionError: If directory is missing or not a directory
        """
        public_avatars = REPO_ROOT / "public" / "avatars"
        assert public_avatars.exists(), "public/avatars directory not found"
        assert public_avatars.is_dir(), "public/avatars is not a directory"

    def test_watchdog_script_exists(self):
        """Test that watchdog script exists and has correct logic.
        
        Validates watchdog.sh contains activity tracking and shutdown commands.
        """
        watchdog = REPO_ROOT / "watchdog.sh"
        assert watchdog.exists(), "watchdog.sh not found"
        content = watchdog.read_text()
        assert "activity.last" in content, "watchdog.sh missing activity.last reference"
        assert "docker compose down" in content, "watchdog.sh missing docker compose down command"
        assert "#!/bin/bash" in content, "watchdog.sh missing shebang"

    def test_setup_scripts_exist(self):
        """Test that setup scripts exist.
        
        Validates presence and content of setup.sh and setup_git.sh scripts.
        """
        assert (REPO_ROOT / "setup.sh").exists(), "setup.sh not found"
        assert (REPO_ROOT / "setup_git.sh").exists(), "setup_git.sh not found"
        
        setup = (REPO_ROOT / "setup.sh").read_text()
        assert "venv" in setup, "setup.sh missing venv creation"
        assert "requirements.txt" in setup, "setup.sh missing requirements installation"

    def test_github_workflow_exists(self):
        """Test that GitHub Actions workflow exists.
        
        Verifies workflow contains pytest, dmz branch reference, and merge job.
        """
        workflow = REPO_ROOT / ".github" / "workflows" / "test.yml"
        assert workflow.exists(), "GitHub Actions workflow not found"
        content = workflow.read_text()
        assert "pytest" in content, "Workflow missing pytest"
        assert "dmz" in content, "Workflow missing dmz branch reference"
        assert "merge" in content.lower(), "Workflow missing merge job"

    def test_gitignore_has_python_patterns(self):
        """Test that .gitignore ignores Python cache files.
        
        Validates .gitignore contains __pycache__ and .pytest_cache patterns.
        """
        gitignore = REPO_ROOT / ".gitignore"
        assert gitignore.exists(), ".gitignore not found"
        content = gitignore.read_text()
        assert "__pycache__" in content, ".gitignore missing __pycache__"
        assert ".pytest_cache" in content, ".gitignore missing .pytest_cache"

    def test_multiple_characters_exist(self):
        """Test that multiple characters exist for dropdown functionality.
        
        Requires at least 2 characters for profile dropdown to appear.
        """
        char_files = list((REPO_ROOT / "characters").glob("*.json"))
        assert len(char_files) >= 2, "Need at least 2 characters for dropdown to appear"

    def test_env_template_files_exist(self):
        """Test that .env.template files exist for both services.
        
        Validates both webbui_chat and characters_api have template files.
        """
        webbui_template = REPO_ROOT / "webbui_chat" / ".env.template"
        api_template = REPO_ROOT / "characters_api" / ".env.template"
        root_template = REPO_ROOT / ".env.template"
        
        assert webbui_template.exists(), "webbui_chat/.env.template not found"
        assert api_template.exists(), "characters_api/.env.template not found"
        assert root_template.exists(), "Root .env.template not found"
        
        # Validate required fields in webbui template
        webbui_content = webbui_template.read_text()
        assert "CHAT_API_URL=" in webbui_content, "webbui_chat template missing CHAT_API_URL"
        assert "MODELS_API_URL=" in webbui_content, "webbui_chat template missing MODELS_API_URL"
        
        # Validate required fields in API template
        api_content = api_template.read_text()
        assert "CHAR_API_KEY=" in api_content, "characters_api template missing CHAR_API_KEY"
        assert "HOST_URL=" in api_content, "characters_api template missing HOST_URL"

    def test_docker_compose_consistency(self):
        """Test that docker-compose files have consistent volume mounts.
        
        Validates both services mount shared directories correctly.
        """
        webbui_compose = REPO_ROOT / "webbui_chat" / "docker-compose.yaml"
        api_compose = REPO_ROOT / "characters_api" / "docker-compose.yaml"
        
        assert webbui_compose.exists(), "webbui_chat docker-compose.yaml not found"
        assert api_compose.exists(), "characters_api docker-compose.yaml not found"
        
        webbui_content = webbui_compose.read_text()
        api_content = api_compose.read_text()
        
        # Both should mount activity tracking
        assert "/tmp/activity.last:/tmp/activity.last" in webbui_content, "webbui_chat missing activity volume"
        
        # Both should mount shared directories
        assert "../characters:" in webbui_content, "webbui_chat missing characters volume"
        assert "../public:" in webbui_content, "webbui_chat missing public volume"
        assert "../characters:" in api_content, "characters_api missing characters volume"
        assert "../public:" in api_content, "characters_api missing public volume"