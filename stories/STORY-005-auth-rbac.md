# STORY-005 · Authentication & Role-Based Access Control

## Overview
Implement production-ready authentication per the MVP: persist users in PostgreSQL, hash passwords securely, expose JWT-based login/registration flows, and gate APIs by role (`admin`, `analyst`, `viewer`).

## Acceptance Criteria
- `User` model persists hashed passwords, role, and active flag (reuse existing SQLAlchemy model, ensure migrations run).
- `POST /api/auth/register` creates users (admin-only), `POST /api/auth/login` returns JWT with `sub`, `role`, and expiration, `POST /api/auth/logout` invalidates token client-side.
- Dependency `require_role` enforces minimum role on protected endpoints (e.g., uploads require `analyst`, user admin requires `admin`).
- Password hashing uses `passlib` with bcrypt or argon2 (configurable).
- Tests cover login success/failure, role protection, and token expiry.

## Auth Service Mockup
```python
# backend/services/auth_service.py
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_access_token(*, user_id: int, role: str, expires_minutes: int) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
```

## Router Mockup
```python
# backend/api/auth.py
@router.post("/register", response_model=Token, dependencies=[Depends(require_role("admin"))])
def register_user(request: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        role=request.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.id, role=user.role, expires_minutes=settings.access_token_expire_minutes)
    return Token(access_token=token, token_type="bearer")

@router.post("/login", response_model=Token)
def login_user(request: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token(user_id=user.id, role=user.role, expires_minutes=settings.access_token_expire_minutes)
    return Token(access_token=token, token_type="bearer")
```

## Role Guard Mockup
```python
# backend/middleware/role_access.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import jwt

security = HTTPBearer()

def require_role(*allowed_roles: str):
    def _checker(credentials = Depends(security)):
        try:
            payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
            role = payload.get("role")
            if role not in allowed_roles:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
            return payload
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return _checker
```

## Integration Notes
- Apply `Depends(require_role("analyst", "admin"))` to ingestion routes.
- Add `Depends(require_role("admin"))` to job listings if only admins can see history.
- Seed initial admin via `db/init.sql` or migration with hashed password.
- Update frontend to store JWT in secure storage (HTTP-only cookie or localStorage for MVP) and attach Authorization header to protected calls.

