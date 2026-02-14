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


def test_character_json_structure():
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


def test_system_prompt_files_exist():
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


def test_avatar_files_exist():
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


def test_public_avatars_directory():
    """Test that public/avatars directory exists.
    
    :raises AssertionError: If directory is missing or not a directory
    """
    public_avatars = REPO_ROOT / "public" / "avatars"
    assert public_avatars.exists(), "public/avatars directory not found"
    assert public_avatars.is_dir(), "public/avatars is not a directory"


def test_watchdog_script_exists():
    """Test that watchdog script exists and has correct logic.
    
    Validates watchdog.sh contains activity tracking and shutdown commands.
    """
    watchdog = REPO_ROOT / "watchdog.sh"
    assert watchdog.exists(), "watchdog.sh not found"
    content = watchdog.read_text()
    assert "last_activity" in content, "watchdog.sh missing last_activity reference"
    assert "docker compose down" in content, "watchdog.sh missing docker compose down command"
    assert "#!/bin/bash" in content, "watchdog.sh missing shebang"


def test_setup_scripts_exist():
    """Test that setup scripts exist.
    
    Validates presence and content of setup.sh and setup_git.sh scripts.
    """
    assert (REPO_ROOT / "setup.sh").exists(), "setup.sh not found"
    assert (REPO_ROOT / "setup_git.sh").exists(), "setup_git.sh not found"
    
    setup = (REPO_ROOT / "setup.sh").read_text()
    assert "venv" in setup, "setup.sh missing venv creation"
    assert "requirements.txt" in setup, "setup.sh missing requirements installation"


def test_github_workflow_exists():
    """Test that GitHub Actions workflow exists.
    
    Verifies workflow contains pytest, dmz branch reference, and merge job.
    """
    workflow = REPO_ROOT / ".github" / "workflows" / "test.yml"
    assert workflow.exists(), "GitHub Actions workflow not found"
    content = workflow.read_text()
    assert "pytest" in content, "Workflow missing pytest"
    assert "dmz" in content, "Workflow missing dmz branch reference"
    assert "merge" in content.lower(), "Workflow missing merge job"


def test_gitignore_has_python_patterns():
    """Test that .gitignore ignores Python cache files.
    
    Validates .gitignore contains __pycache__ and .pytest_cache patterns.
    """
    gitignore = REPO_ROOT / ".gitignore"
    assert gitignore.exists(), ".gitignore not found"
    content = gitignore.read_text()
    assert "__pycache__" in content, ".gitignore missing __pycache__"
    assert ".pytest_cache" in content, ".gitignore missing .pytest_cache"


def test_multiple_characters_exist():
    """Test that multiple characters exist for dropdown functionality.
    
    Requires at least 2 characters for profile dropdown to appear.
    """
    char_files = list((REPO_ROOT / "characters").glob("*.json"))
    assert len(char_files) >= 2, "Need at least 2 characters for dropdown to appear"
