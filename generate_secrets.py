#!/usr/bin/env python3
"""Generate authentication secrets for cathyAI.

Utility script to generate secure random secrets for
CHAINLIT_AUTH_SECRET and USER_ADMIN_API_KEY.
"""

import secrets

print("# Add these to webbui_chat/.env")
print()
print(f"CHAINLIT_AUTH_SECRET={secrets.token_urlsafe(48)}")
print(f"USER_ADMIN_API_KEY={secrets.token_urlsafe(32)}")
print()
print("# Keep these secure and never commit to git!")
