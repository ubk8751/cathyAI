"""Auth API for user registration and management."""

import os
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from users import create_user, disable_user, enable_user, create_invite, list_users, verify_user, set_role
from users import init_db
init_db()

app = FastAPI(title="cathyAI Auth API")

REGISTRATION_ENABLED = os.getenv("REGISTRATION_ENABLED", "1") == "1"
REGISTRATION_REQUIRE_INVITE = os.getenv("REGISTRATION_REQUIRE_INVITE", "1") == "1"
USER_ADMIN_API_KEY = os.getenv("USER_ADMIN_API_KEY", "")

def verify_admin(x_admin_key: str = Header(None)):
    """Verify admin API key.
    
    :param x_admin_key: Admin API key from x-admin-key header
    :type x_admin_key: str
    :raises HTTPException: 403 if key is invalid or missing
    """
    if not USER_ADMIN_API_KEY or x_admin_key != USER_ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    invite_code: str = None

class DisableUserRequest(BaseModel):
    username: str

class EnableUserRequest(BaseModel):
    username: str

class SetRoleRequest(BaseModel):
    username: str
    role: str

class CreateInviteRequest(BaseModel):
    expires_hours: int = None

@app.get("/health")
def health():
    """Health check endpoint.
    
    :return: Status dictionary
    :rtype: dict
    """
    return {"ok": True, "service": "auth_api"}

@app.post("/auth/login")
def login(req: LoginRequest):
    """Verify user credentials.
    
    :param req: Login request with username and password
    :type req: LoginRequest
    :return: Success response with user role
    :rtype: dict
    :raises HTTPException: 401 if credentials invalid
    """
    ok, role = verify_user(req.username, req.password)
    if not ok:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"ok": True, "role": role}

@app.post("/auth/register")
def register(req: RegisterRequest):
    """Register new user.
    
    Requires invite code if REGISTRATION_REQUIRE_INVITE=1.
    
    :param req: Registration request with username, password, invite_code
    :type req: RegisterRequest
    :return: Success response
    :rtype: dict
    :raises HTTPException: 403 if registration disabled, 400 if validation fails
    """
    if not REGISTRATION_ENABLED:
        raise HTTPException(status_code=403, detail="Registration disabled")
    
    if REGISTRATION_REQUIRE_INVITE and not req.invite_code:
        raise HTTPException(status_code=400, detail="Invite code required")
    
    success, message = create_user(
        req.username,
        req.password,
        role="user",
        invite_code=req.invite_code if REGISTRATION_REQUIRE_INVITE else None
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"ok": True, "message": message}

@app.post("/auth/admin/disable")
def admin_disable(req: DisableUserRequest, _admin=Header(default=None, alias="x-admin-key")):
    """Disable user (admin only).
    
    :param req: Request with username to disable
    :type req: DisableUserRequest
    :param _admin: Admin API key from header
    :type _admin: str
    :return: Success response
    :rtype: dict
    :raises HTTPException: 403 if not admin, 404 if user not found
    """
    verify_admin(_admin)
    
    success, message = disable_user(req.username)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    
    return {"ok": True, "message": message}

@app.post("/auth/admin/enable")
def admin_enable(req: EnableUserRequest, _admin=Header(default=None, alias="x-admin-key")):
    """Enable user (admin only).
    
    :param req: Request with username to enable
    :type req: EnableUserRequest
    :param _admin: Admin API key from header
    :type _admin: str
    :return: Success response
    :rtype: dict
    :raises HTTPException: 403 if not admin, 404 if user not found
    """
    verify_admin(_admin)
    
    success, message = enable_user(req.username)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    
    return {"ok": True, "message": message}

@app.post("/auth/admin/invite")
def admin_invite(req: CreateInviteRequest, _admin=Header(default=None, alias="x-admin-key")):
    """Create invite code (admin only).
    
    :param req: Request with optional expires_hours
    :type req: CreateInviteRequest
    :param _admin: Admin API key from header
    :type _admin: str
    :return: Response with generated invite code
    :rtype: dict
    :raises HTTPException: 403 if not admin
    """
    verify_admin(_admin)
    
    code = create_invite(req.expires_hours)
    return {"ok": True, "code": code}

@app.get("/auth/admin/users")
def admin_list_users(_admin: str = Header(None, alias="x-admin-key")):
    """List all users (admin only).
    
    :param _admin: Admin API key from header
    :type _admin: str
    :return: Response with list of users
    :rtype: dict
    :raises HTTPException: 403 if not admin
    """
    verify_admin(_admin)
    
    users = list_users()
    return {"ok": True, "users": users}

@app.post("/auth/admin/set_role")
def admin_set_role(req: SetRoleRequest, _admin: str = Header(None, alias="x-admin-key")):
    """Set user role (admin only).
    
    :param req: Request with username and role
    :type req: SetRoleRequest
    :param _admin: Admin API key from header
    :type _admin: str
    :return: Success response
    :rtype: dict
    :raises HTTPException: 403 if not admin, 400 if invalid role, 404 if user not found
    """
    verify_admin(_admin)
    
    success, message = set_role(req.username, req.role)
    if not success:
        raise HTTPException(status_code=400 if "must be" in message else 404, detail=message)
    
    return {"ok": True, "message": message}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
