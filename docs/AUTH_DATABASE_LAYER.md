# Phase 1.2: Auth Database Layer

## Overview

The authentication system now uses the database for persistent storage:

- **User Management**: Users stored in `auth_users` table
- **Session Management**: Active sessions tracked in `user_sessions` table
- **Token Blacklisting**: Revoked tokens in `token_blacklist` table
- **Audit Logging**: All auth actions logged in `user_audit_logs` table
- **MFA Support**: TOTP devices stored in `mfa_devices` table
- **API Keys**: Service account keys in `api_keys` table

## Database Schema

### Tables

```sql
-- Users table
auth_users:
  - id, username, email, hashed_password
  - role (super_admin, admin, security_analyst, user, viewer, api_service)
  - is_active, is_verified, is_mfa_enabled
  - failed_login_attempts, locked_until
  - last_login_at, last_login_ip
  - created_at, updated_at

-- Sessions table
user_sessions:
  - id, user_id, session_id, refresh_token_jti
  - ip_address, user_agent, device_info
  - is_active, revoked, revoked_reason
  - created_at, expires_at, last_activity_at, revoked_at

-- Token blacklist
token_blacklist:
  - id, jti, token_type, user_id
  - reason, revoked_at, expires_at

-- MFA devices
mfa_devices:
  - id, user_id, device_type, name
  - secret (encrypted), backup_codes (hashed)
  - is_active, is_primary, verified
  - created_at, last_used_at

-- API keys
api_keys:
  - id, user_id, key_id, key_hash, key_prefix
  - name, description, scopes
  - rate_limit, is_active, expires_at
  - use_count, last_used_at
  - created_at, revoked_at

-- Audit logs
user_audit_logs:
  - id, user_id, action, action_category
  - ip_address, user_agent, session_id
  - details (JSON), result, failure_reason
  - timestamp
```

## Files Added/Modified

### New Files
- `database/auth_models.py` - Database models for auth system
- `auth/user_manager.py` - Database-backed user management
- `tests/test_auth_database.py` - Database layer tests

### Modified Files
- `auth/__init__.py` - Added UserManager exports
- `api/main.py` - Integrated database-backed auth

## API Changes

### New Endpoints
```
POST /auth/logout           - Revoke current session
POST /auth/logout-all       - Revoke all user sessions
```

### Updated Endpoints
```
POST /auth/login            - Now creates database session
POST /auth/refresh          - Validates against database
```

## Configuration

Environment variables:
```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-min-32-bytes
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=sqlite:///./zen_pentest.db
# or
DATABASE_URL=postgresql://user:pass@localhost:5432/zen_pentest
```

## Usage Examples

### User Authentication
```python
from database.auth_models import get_auth_db
from auth.user_manager import get_user_manager

db = next(get_auth_db())
user_manager = get_user_manager()

# Authenticate
user = user_manager.authenticate_user(db, "username", "password")

# Create session
session_data = user_manager.create_session(db, user, ip_address, user_agent)
# Returns: {access_token, refresh_token, session_id, token_type, expires_in}

# Refresh token
new_tokens = user_manager.refresh_session(db, refresh_token)

# Revoke session
user_manager.revoke_session(db, session_id, "logout")

# Revoke all sessions
user_manager.revoke_all_user_sessions(db, user.id, "security")
```

### User Management
```python
# Create user
from database.auth_models import UserRole
create_user(db, "newuser", "new@example.com", hashed_password, UserRole.USER)

# Change password
user_manager.change_password(db, user_id, old_password, new_password)

# Deactivate user
user_manager.deactivate_user(db, user_id)

# Update role
user_manager.update_user_role(db, user_id, UserRole.ADMIN)
```

### Audit Logging
```python
# Get user audit logs
logs = user_manager.get_user_audit_logs(db, user_id, limit=100)

# Audit log is automatically populated by:
# - authenticate_user (login attempts)
# - change_password
# - create_session
# - revoke_session
# - deactivate_user
```

## Test Results

```
Database Layer Tests: 17 passed
Auth Module Tests:    30 passed  
Integration Tests:    12 passed
Legacy Tests:          7 passed
─────────────────────────────────
Total:                66 passed
```

## Migration Guide

### From Legacy Auth
1. Default admin user is auto-created on startup
2. Old JWT tokens still work until they expire
3. New sessions are stored in database

### Database Migration
```bash
# Initialize auth tables
python -c "from database.auth_models import init_auth_db; init_auth_db()"

# Or let the API do it automatically on startup
python api/main.py
```

## Security Features

1. **Account Lockout**: 5 failed attempts = 30 min lockout
2. **Password History**: Last 5 passwords cannot be reused
3. **Session Tracking**: IP, user agent, device fingerprinting
4. **Token Blacklisting**: Immediate revocation support
5. **Concurrent Session Limits**: Can be enforced per user
6. **Audit Trail**: All authentication events logged

## Next Steps (Phase 1.3)

- MFA enrollment endpoints
- API key management endpoints
- Session management UI
- Advanced audit log viewer
- Rate limiting per user/session
