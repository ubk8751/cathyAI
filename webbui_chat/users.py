"""User management with SQLite and bcrypt."""

import sqlite3
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from passlib.hash import bcrypt

USER_DB_PATH = Path(os.getenv("USER_DB_PATH", "/state/users.sqlite"))

def init_db():
    """Initialize database schema if not exists.
    
    Creates users and invites tables with proper schema.
    Safe to call multiple times (uses IF NOT EXISTS).
    """
    USER_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(USER_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            pw_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            last_login_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invites (
            code TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            used_by TEXT,
            used_at TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

def create_user(username: str, password: str, role: str = "user", invite_code: str = None) -> tuple[bool, str]:
    """Create new user.
    
    :param username: Unique username for the account
    :type username: str
    :param password: Plaintext password (will be hashed with bcrypt)
    :type password: str
    :param role: User role (admin or user), defaults to user
    :type role: str
    :param invite_code: Optional invite code for registration
    :type invite_code: str or None
    :return: Tuple of (success, message)
    :rtype: tuple[bool, str]
    """
    init_db()
    conn = sqlite3.connect(USER_DB_PATH)
    
    # Check if user exists
    existing = conn.execute("SELECT username FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        conn.close()
        return False, "Username already exists"
    
    # Validate invite if required
    if invite_code:
        invite = conn.execute(
            "SELECT code, expires_at, used_by, is_active FROM invites WHERE code = ?",
            (invite_code,)
        ).fetchone()
        
        if not invite:
            conn.close()
            return False, "Invalid invite code"
        
        if not invite[3]:  # is_active
            conn.close()
            return False, "Invite code already used"
        
        if invite[1]:  # expires_at
            if datetime.fromisoformat(invite[1]) < datetime.utcnow():
                conn.close()
                return False, "Invite code expired"
        
        # Mark invite as used
        conn.execute(
            "UPDATE invites SET used_by = ?, used_at = ?, is_active = 0 WHERE code = ?",
            (username, datetime.utcnow().isoformat(), invite_code)
        )
    
    # Create user
    pw_hash = bcrypt.hash(password)
    conn.execute(
        "INSERT INTO users (username, pw_hash, role, created_at) VALUES (?, ?, ?, ?)",
        (username, pw_hash, role, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    return True, "User created"

def verify_user(username: str, password: str) -> tuple[bool, str]:
    """Verify user credentials.
    
    :param username: Username to verify
    :type username: str
    :param password: Plaintext password to check
    :type password: str
    :return: Tuple of (success, role). Role is empty string if verification fails
    :rtype: tuple[bool, str]
    """
    init_db()
    conn = sqlite3.connect(USER_DB_PATH)
    
    user = conn.execute(
        "SELECT pw_hash, role, is_active FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    
    if not user:
        conn.close()
        return False, ""
    
    pw_hash, role, is_active = user
    
    if not is_active:
        conn.close()
        return False, ""
    
    if not bcrypt.verify(password, pw_hash):
        conn.close()
        return False, ""
    
    # Update last login
    conn.execute(
        "UPDATE users SET last_login_at = ? WHERE username = ?",
        (datetime.utcnow().isoformat(), username)
    )
    conn.commit()
    conn.close()
    
    return True, role

def disable_user(username: str) -> tuple[bool, str]:
    """Disable user account.
    
    Sets is_active=0 to prevent login. Does not delete user data.
    
    :param username: Username to disable
    :type username: str
    :return: Tuple of (success, message)
    :rtype: tuple[bool, str]
    """
    init_db()
    conn = sqlite3.connect(USER_DB_PATH)
    
    result = conn.execute(
        "UPDATE users SET is_active = 0 WHERE username = ?",
        (username,)
    )
    conn.commit()
    
    if result.rowcount == 0:
        conn.close()
        return False, "User not found"
    
    conn.close()
    return True, "User disabled"

def enable_user(username: str) -> tuple[bool, str]:
    """Enable user account.
    
    Sets is_active=1 to allow login again.
    
    :param username: Username to enable
    :type username: str
    :return: Tuple of (success, message)
    :rtype: tuple[bool, str]
    """
    init_db()
    conn = sqlite3.connect(USER_DB_PATH)
    
    result = conn.execute(
        "UPDATE users SET is_active = 1 WHERE username = ?",
        (username,)
    )
    conn.commit()
    
    if result.rowcount == 0:
        conn.close()
        return False, "User not found"
    
    conn.close()
    return True, "User enabled"

def create_invite(expires_hours: int = None) -> str:
    """Create invite code.
    
    :param expires_hours: Optional expiration time in hours
    :type expires_hours: int or None
    :return: Generated invite code
    :rtype: str
    """
    init_db()
    code = secrets.token_urlsafe(12)
    expires_at = None
    if expires_hours:
        expires_at = (datetime.utcnow() + timedelta(hours=expires_hours)).isoformat()
    
    conn = sqlite3.connect(USER_DB_PATH)
    conn.execute(
        "INSERT INTO invites (code, created_at, expires_at) VALUES (?, ?, ?)",
        (code, datetime.utcnow().isoformat(), expires_at)
    )
    conn.commit()
    conn.close()
    
    return code

def list_users() -> list[dict]:
    """List all users with metadata.
    
    :return: List of user dictionaries with username, role, is_active, created_at, last_login_at
    :rtype: list[dict]
    """
    init_db()
    conn = sqlite3.connect(USER_DB_PATH)
    conn.row_factory = sqlite3.Row
    
    rows = conn.execute(
        "SELECT username, role, is_active, created_at, last_login_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    
    conn.close()
    return [dict(row) for row in rows]
