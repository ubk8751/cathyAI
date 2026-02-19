"""Bootstrap admin user.

Command-line utility to create initial admin user account.
Usage: python bootstrap_admin.py <username>
"""

import sys
import getpass
from users import create_user, init_db

def main():
    """Create admin user from command line.
    
    Prompts for password securely and creates admin account.
    Exits with code 1 on failure.
    """
    if len(sys.argv) < 2:
        print("Usage: python bootstrap_admin.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    password = getpass.getpass(f"Password for {username}: ")
    
    if not password:
        print("Password cannot be empty")
        sys.exit(1)
    
    init_db()
    success, message = create_user(username, password, role="admin", invite_code=None)
    
    if success:
        print(f"✅ Admin user '{username}' created successfully")
    else:
        print(f"❌ Failed: {message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
