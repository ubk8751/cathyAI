"""Functional tests for user authentication system.

Tests actual user management operations including registration,
login verification, invite codes, and admin operations.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path

# Get repo root
REPO_ROOT = Path(__file__).parent.parent

# Set test database path before importing users module
test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite')
test_db.close()
os.environ['USER_DB_PATH'] = test_db.name

import sys
sys.path.insert(0, str(REPO_ROOT / "webbui_chat"))

from users import (
    init_db, create_user, verify_user, disable_user, enable_user,
    create_invite, list_users
)


class TestAuthModules:
    """Test suite for authentication module existence and structure."""
    
    def test_auth_modules_exist(self):
        """Test that authentication modules exist."""
        users_py = REPO_ROOT / "webbui_chat" / "users.py"
        auth_api_py = REPO_ROOT / "webbui_chat" / "auth_api.py"
        bootstrap_py = REPO_ROOT / "webbui_chat" / "bootstrap_admin.py"
        
        assert users_py.exists(), "users.py not found"
        assert auth_api_py.exists(), "auth_api.py not found"
        assert bootstrap_py.exists(), "bootstrap_admin.py not found"
    
    def test_user_management_docs_exist(self):
        """Test that user management documentation exists."""
        user_mgmt_doc = REPO_ROOT / "webbui_chat" / "USER_MANAGEMENT.md"
        assert user_mgmt_doc.exists(), "USER_MANAGEMENT.md not found"
    
    def test_auth_dependencies_in_requirements(self):
        """Test that auth dependencies are in requirements.txt."""
        requirements = REPO_ROOT / "webbui_chat" / "requirements.txt"
        content = requirements.read_text()
        
        assert "fastapi" in content, "fastapi not in requirements.txt"
        assert "uvicorn" in content, "uvicorn not in requirements.txt"
        assert "passlib" in content, "passlib not in requirements.txt"
        assert "bcrypt" in content, "bcrypt not in requirements.txt"
    
    def test_auth_env_vars_in_template(self):
        """Test that auth environment variables are in template."""
        env_template = REPO_ROOT / "webbui_chat" / ".env.template"
        content = env_template.read_text()
        
        assert "CHAINLIT_AUTH_SECRET" in content, "CHAINLIT_AUTH_SECRET not in .env.template"
        assert "USER_DB_PATH" in content, "USER_DB_PATH not in .env.template"
        assert "USER_ADMIN_API_KEY" in content, "USER_ADMIN_API_KEY not in .env.template"
        assert "REGISTRATION_ENABLED" in content, "REGISTRATION_ENABLED not in .env.template"
        assert "REGISTRATION_REQUIRE_INVITE" in content, "REGISTRATION_REQUIRE_INVITE not in .env.template"


class TestUserAuthentication:
    """Test suite for user authentication functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Setup: initialize fresh database
        init_db()
        yield
        # Teardown: clean up test database
        try:
            os.unlink(test_db.name)
        except:
            pass
    
    def test_create_user_without_invite(self):
        """Test creating user without invite code."""
        success, message = create_user("testuser", "password123", role="user")
        assert success is True
        assert message == "User created"
    
    def test_create_user_duplicate_username(self):
        """Test that duplicate usernames are rejected."""
        create_user("testuser", "password123")
        success, message = create_user("testuser", "different_password")
        assert success is False
        assert "already exists" in message.lower()
    
    def test_verify_user_correct_password(self):
        """Test user verification with correct password."""
        create_user("testuser", "password123", role="admin")
        success, role = verify_user("testuser", "password123")
        assert success is True
        assert role == "admin"
    
    def test_verify_user_wrong_password(self):
        """Test user verification with wrong password."""
        create_user("testuser", "password123")
        success, role = verify_user("testuser", "wrong_password")
        assert success is False
        assert role == ""
    
    def test_verify_nonexistent_user(self):
        """Test verification of user that doesn't exist."""
        success, role = verify_user("nonexistent", "password")
        assert success is False
        assert role == ""
    
    def test_disable_user(self):
        """Test disabling a user account."""
        create_user("testuser", "password123")
        
        # Verify user can login before disable
        success, _ = verify_user("testuser", "password123")
        assert success is True
        
        # Disable user
        success, message = disable_user("testuser")
        assert success is True
        assert "disabled" in message.lower()
        
        # Verify user cannot login after disable
        success, _ = verify_user("testuser", "password123")
        assert success is False
    
    def test_enable_user(self):
        """Test re-enabling a disabled user account."""
        create_user("testuser", "password123")
        disable_user("testuser")
        
        # Enable user
        success, message = enable_user("testuser")
        assert success is True
        assert "enabled" in message.lower()
        
        # Verify user can login again
        success, _ = verify_user("testuser", "password123")
        assert success is True
    
    def test_disable_nonexistent_user(self):
        """Test disabling user that doesn't exist."""
        success, message = disable_user("nonexistent")
        assert success is False
        assert "not found" in message.lower()
    
    def test_create_invite_code(self):
        """Test creating invite code."""
        code = create_invite()
        assert code is not None
        assert len(code) > 0
    
    def test_create_invite_with_expiry(self):
        """Test creating invite code with expiration."""
        code = create_invite(expires_hours=24)
        assert code is not None
        assert len(code) > 0
    
    def test_register_with_valid_invite(self):
        """Test user registration with valid invite code."""
        invite_code = create_invite()
        success, message = create_user("testuser", "password123", invite_code=invite_code)
        assert success is True
        assert message == "User created"
    
    def test_register_with_invalid_invite(self):
        """Test user registration with invalid invite code."""
        success, message = create_user("testuser", "password123", invite_code="invalid_code")
        assert success is False
        assert "invalid" in message.lower()
    
    def test_invite_single_use(self):
        """Test that invite codes can only be used once."""
        invite_code = create_invite()
        
        # First use should succeed
        success, _ = create_user("user1", "password123", invite_code=invite_code)
        assert success is True
        
        # Second use should fail
        success, message = create_user("user2", "password123", invite_code=invite_code)
        assert success is False
        assert "used" in message.lower() or "invalid" in message.lower()
    
    def test_list_users(self):
        """Test listing all users."""
        create_user("user1", "password1", role="admin")
        create_user("user2", "password2", role="user")
        
        users = list_users()
        assert len(users) == 2
        assert any(u['username'] == 'user1' and u['role'] == 'admin' for u in users)
        assert any(u['username'] == 'user2' and u['role'] == 'user' for u in users)
    
    def test_user_roles(self):
        """Test that user roles are preserved."""
        create_user("admin_user", "password", role="admin")
        create_user("regular_user", "password", role="user")
        
        success, role = verify_user("admin_user", "password")
        assert role == "admin"
        
        success, role = verify_user("regular_user", "password")
        assert role == "user"
    
    def test_password_hashing(self):
        """Test that passwords are hashed, not stored in plaintext."""
        create_user("testuser", "password123")
        
        # Check database directly
        conn = sqlite3.connect(test_db.name)
        cursor = conn.execute("SELECT pw_hash FROM users WHERE username = ?", ("testuser",))
        pw_hash = cursor.fetchone()[0]
        conn.close()
        
        # Hash should not equal plaintext password
        assert pw_hash != "password123"
        # Hash should be bcrypt format
        assert pw_hash.startswith("$2b$")
    
    def test_last_login_tracking(self):
        """Test that last login timestamp is updated."""
        create_user("testuser", "password123")
        
        # First login
        verify_user("testuser", "password123")
        
        # Check last_login_at is set
        conn = sqlite3.connect(test_db.name)
        cursor = conn.execute("SELECT last_login_at FROM users WHERE username = ?", ("testuser",))
        last_login = cursor.fetchone()[0]
        conn.close()
        
        assert last_login is not None
        assert len(last_login) > 0
    
    def test_user_metadata_in_list(self):
        """Test that list_users returns complete metadata."""
        create_user("testuser", "password123", role="admin")
        
        users = list_users()
        user = users[0]
        
        assert 'username' in user
        assert 'role' in user
        assert 'is_active' in user
        assert 'created_at' in user
        assert user['username'] == 'testuser'
        assert user['role'] == 'admin'
        assert user['is_active'] == 1
