# STORY-005 · Authentication & Role-Based Access Control

## Status
✅ Completed

## Overview
Users authenticate against the platform with email/password credentials stored in PostgreSQL and receive short-lived JWTs that encode their role. Protected routes enforce `admin`, `analyst`, or `viewer` roles so ingestion features remain gated to the right operators.

## Delivered Capabilities
- `backend/models/user.py` persists users with hashed passwords (`pbkdf2_sha256` via Passlib), role defaults, and active flag.
- `POST /api/auth/register` (admin only) and `POST /api/auth/login` issue JWTs containing `sub`, `role`, and expiry claims using `python-jose`. The tokens honour the `SECRET_KEY` and `ACCESS_TOKEN_EXPIRE_MINUTES` settings.
- `require_role` in `backend/api/auth.py` wraps the FastAPI `HTTPBearer` dependency and rejects missing/expired tokens or insufficient roles with appropriate HTTP codes.
- Core ingestion APIs (`/api/upload/file`, `/api/data-ingest`, `/api/jira/ingest`, etc.) all apply `Depends(require_role("analyst", "admin"))`, while registration stays admin only.
- `backend/scripts/migrate_database.py` seeds a default `admin@example.com` account to simplify local bootstrap.

## Reference Implementation
- Auth router & utilities: `backend/api/auth.py`
- User model: `backend/models/user.py`
- JWT helpers: `backend/api/auth.py:create_access_token`, `verify_token`, `require_role`
- Settings: `backend/config.py` (secret key, algorithm, token expiry)

## Verification
- `test_basic.py:test_auth_logic` exercises hashing and token generation.
- Frontend login form (`client/src/pages/Login/Login.js`) authenticates, stores the bearer token, and redirects based on success.

## Follow-ups
- Add token refresh/rotation and revoke logic if long-lived sessions become a requirement.
