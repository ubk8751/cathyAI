"""Bootstrap admin user.

Automatic admin account creation on first startup.
Runs once if database is empty and bootstrap env vars are set.
"""

import os
from users import count_users, upsert_user

def bootstrap():
    """Create initial admin user if database is empty.
    
    Only runs if BOOTSTRAP_ADMIN_USERNAME and BOOTSTRAP_ADMIN_PASSWORD
    are set and the database has no users yet.
    """
    username = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "").strip()
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "").strip()

    if not username or not password:
        print("bootstrap_admin: BOOTSTRAP_ADMIN_USERNAME/PASSWORD not set; skipping")
        return

    # only bootstrap if DB is empty (safe default)
    if count_users() > 0:
        print("bootstrap_admin: users already exist; skipping")
        return

    ok, msg = upsert_user(username, password, role="admin")
    print(f"bootstrap_admin: {ok} {msg}")

if __name__ == "__main__":
    bootstrap()
