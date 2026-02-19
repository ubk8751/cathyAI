# User Management Guide

## Overview

cathyAI now includes user authentication with registration and admin management capabilities. Users are stored in SQLite with bcrypt password hashing.

## Architecture

```
┌──────────────────┐         ┌─────────────────┐
│  webbui_chat     │         │ webbui_auth_api │
│  (Chainlit UI)   │         │  (FastAPI)      │
│  Port 8000       │         │  Port 8001      │
└────────┬─────────┘         └────────┬────────┘
         │                            │
         └────────────┬───────────────┘
                      │
                      ▼
              /state/users.sqlite
```

## Setup

### 1. Generate Secrets

```bash
python3 - <<'PY'
import secrets
print("CHAINLIT_AUTH_SECRET=" + secrets.token_urlsafe(48))
print("USER_ADMIN_API_KEY=" + secrets.token_urlsafe(32))
PY
```

### 2. Update .env

Add to `.env`:

```bash
# Chainlit authentication
CHAINLIT_AUTH_SECRET=<generated_secret>

# User management
USER_DB_PATH=/state/users.sqlite
REGISTRATION_ENABLED=1
REGISTRATION_REQUIRE_INVITE=1
USER_ADMIN_API_KEY=<generated_key>
```

### 3. Create State Directory

```bash
mkdir -p state
```

### 4. Bootstrap Admin User

```bash
docker compose run --rm webbui_chat python bootstrap_admin.py your_username
# Enter password when prompted
```

### 5. Start Services

```bash
docker compose up -d --build
```

## Usage

### Admin Operations

All admin operations require the `x-admin-key` header with your `USER_ADMIN_API_KEY`.

#### Create Invite Code

```bash
curl -X POST "http://localhost:8001/auth/admin/invite" \
  -H "x-admin-key: YOUR_ADMIN_KEY" \
  -H "content-type: application/json" \
  -d '{"expires_hours": 72}'
```

Response:
```json
{"ok": true, "code": "abc123xyz789"}
```

#### List Users

```bash
curl "http://localhost:8001/auth/admin/users" \
  -H "x-admin-key: YOUR_ADMIN_KEY"
```

#### Disable User

```bash
curl -X POST "http://localhost:8001/auth/admin/disable" \
  -H "x-admin-key: YOUR_ADMIN_KEY" \
  -H "content-type: application/json" \
  -d '{"username": "friend1"}'
```

#### Enable User

```bash
curl -X POST "http://localhost:8001/auth/admin/enable" \
  -H "x-admin-key: YOUR_ADMIN_KEY" \
  -H "content-type: application/json" \
  -d '{"username": "friend1"}'
```

### User Registration

#### Register New User

```bash
curl -X POST "http://localhost:8001/auth/register" \
  -H "content-type: application/json" \
  -d '{
    "username": "friend1",
    "password": "secure_password",
    "invite_code": "abc123xyz789"
  }'
```

Response:
```json
{"ok": true, "message": "User created"}
```

### Login

1. Navigate to `http://localhost:8000`
2. Enter username and password
3. Access chat interface

## Configuration Options

### REGISTRATION_ENABLED

- `1` - Allow new user registration
- `0` - Disable registration (existing users can still login)

### REGISTRATION_REQUIRE_INVITE

- `1` - Require valid invite code for registration
- `0` - Allow open registration (not recommended)

## Security

### Password Storage

- Passwords hashed with bcrypt (cost factor 12)
- Never stored in plaintext
- Secure against rainbow table attacks

### Session Management

- Sessions signed with `CHAINLIT_AUTH_SECRET`
- Rotating secret logs out all users (emergency kill switch)
- Sessions persist across container restarts

### API Protection

- Admin endpoints require `USER_ADMIN_API_KEY`
- Keep port 8001 LAN/Tailscale only
- Consider firewall rules for additional protection

## Database Schema

### users table

| Column | Type | Description |
|--------|------|-------------|
| username | TEXT PRIMARY KEY | Unique username |
| pw_hash | TEXT | bcrypt password hash |
| role | TEXT | User role (admin/user) |
| is_active | INTEGER | 1=active, 0=disabled |
| created_at | TEXT | ISO timestamp |
| last_login_at | TEXT | ISO timestamp |

### invites table

| Column | Type | Description |
|--------|------|-------------|
| code | TEXT PRIMARY KEY | Invite code |
| created_at | TEXT | ISO timestamp |
| expires_at | TEXT | ISO timestamp (nullable) |
| used_by | TEXT | Username who used it |
| used_at | TEXT | ISO timestamp |
| is_active | INTEGER | 1=unused, 0=used |

## Troubleshooting

### Can't login after setup

- Verify `CHAINLIT_AUTH_SECRET` is set
- Check admin user was created: `docker exec -it cathyai-webbui_chat-1 ls -la /state/`
- Check logs: `docker logs cathyai-webbui_chat-1`

### Registration fails

- Verify `REGISTRATION_ENABLED=1`
- Check invite code is valid and not expired
- Ensure username doesn't already exist

### Disabled user still has access

- User may have active session token
- Rotate `CHAINLIT_AUTH_SECRET` to force logout
- Or wait for session to expire

### Auth API not accessible

- Verify port 8001 is mapped in docker-compose.yaml
- Check service is running: `docker ps`
- Check logs: `docker logs cathyai-webbui_auth_api-1`

## Backup

### Backup User Database

```bash
cp state/users.sqlite state/users.sqlite.backup
```

### Restore

```bash
cp state/users.sqlite.backup state/users.sqlite
docker compose restart
```

## Migration from No Auth

If you're adding auth to an existing deployment:

1. Follow setup steps above
2. Bootstrap your admin account
3. Existing sessions will be invalidated
4. Users must login to continue

## Future Enhancements

Potential additions:

- Password reset flow
- Email verification
- Rate limiting on login attempts
- Audit log for admin actions
- Web UI for user management
- OAuth/SSO integration
