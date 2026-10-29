import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(
        "JWT_SECRET_KEY is missing or too short (need 32+ characters). "
        "Generate one with: "
        'python -c "import secrets; print(secrets.token_urlsafe(48))"'
    )

password_hash = PasswordHash.recommended()

# Used to spend the same time hashing when an email does not exist, so login
# timing does not reveal which emails are registered.
_DUMMY_HASH = password_hash.hash("moneymind-dummy-password")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def fake_verify_password(password: str) -> None:
    password_hash.verify(password, _DUMMY_HASH)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {"user_id": user_id, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id


# auto_error=False so a missing header returns 401 (not 403), consistently.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)