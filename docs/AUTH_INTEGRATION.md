# Auth System Integration

## Overview

The new authentication system has been successfully integrated into the API. This provides:

- **JWT Token Authentication** with access and refresh tokens
- **Role-Based Access Control (RBAC)** with 6 roles
- **Multi-Factor Authentication (MFA)** with TOTP support
- **Token Blacklisting** for logout
- **Middleware** for automatic auth validation

## Integration Changes

### 1. API Endpoints (`api/main.py`)

Updated endpoints:
- `POST /auth/login` - Now creates both access and refresh tokens
- `GET /auth/me` - Works with new JWT tokens
- `POST /auth/refresh` - NEW endpoint to refresh access tokens

### 2. Auth Middleware (`auth/middleware.py`)

Added automatic authentication middleware:
- Validates JWT tokens on all protected routes
- Supports public paths configuration
- Stores user info in request state

### 3. Dependencies

New dependency functions:
- `verify_token()` - Unified token verification (new + legacy)
- Future: `require_role()`, `require_permission()` - RBAC dependencies

## Configuration

Required environment variables:

```bash
# Required for new auth system
JWT_SECRET_KEY=your-secret-key-here  # Must be at least 32 bytes for production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Legacy (still works as fallback)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=securepassword123  # Must be >= 6 characters
```

## Token Format

### Access Token
```json
{
  "sub": "username",
  "jti": "unique-token-id",
  "type": "access",
  "roles": ["admin"],
  "permissions": [],
  "exp": 1234567890,
  "iat": 1234567800
}
```

### Refresh Token
```json
{
  "sub": "username",
  "jti": "unique-token-id",
  "type": "refresh",
  "session_id": "session_username",
  "exp": 1239834890,
  "iat": 1234567800
}
```

## Usage

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "username": "admin",
  "role": "admin"
}
```

### Access Protected Endpoint
```bash
curl -X GET http://localhost:8000/scans \
  -H "Authorization: Bearer <access_token>"
```

### Refresh Token
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Authorization: Bearer <refresh_token>"
```

## Roles and Permissions

### Roles
| Role | Description |
|------|-------------|
| `SUPER_ADMIN` | Full system access |
| `ADMIN` | Administrative access |
| `SECURITY_ANALYST` | Can run scans and view findings |
| `USER` | Standard user access |
| `VIEWER` | Read-only access |
| `API_SERVICE` | Service account access |

### Permissions
Permissions are checked against roles. Example:
- `scans:create` - Create new scans
- `findings:read` - View findings
- `reports:delete` - Delete reports

## Testing

Run auth tests:
```bash
# All auth tests
JWT_SECRET_KEY="test-secret" python -m pytest tests/test_auth*.py tests/auth/ -v

# Integration tests only
JWT_SECRET_KEY="test-secret" python -m pytest tests/test_auth_integration.py -v

# Legacy auth tests
python -m pytest tests/test_auth_legacy.py -v
```

## Migration Notes

### Backward Compatibility
- Legacy auth (`api/auth.py`) still works
- Old tokens continue to work during transition
- Both systems can coexist

### Future Enhancements
1. Database-backed user storage (Phase 1.2)
2. MFA enrollment endpoints
3. API key management endpoints
4. Audit logging middleware activation

## Files Changed

- `api/main.py` - Integrated new auth system
- `api/schemas.py` - Added `refresh_token` field
- `auth/middleware.py` - Created FastAPI middleware
- `auth/__init__.py` - Added middleware exports
- `tests/test_auth_integration.py` - NEW integration tests
- `tests/test_auth_legacy.py` - Legacy tests (renamed)

## Test Results

```
49 passed, 10 warnings

- 30 tests: auth module unit tests (JWT, MFA, RBAC, Password)
- 12 tests: API integration tests
- 7 tests: Legacy auth tests
```
