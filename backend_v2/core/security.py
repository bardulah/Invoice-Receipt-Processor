"""Security utilities"""
from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
from jwt import PyJWTError

from .config import settings
from .exceptions import AuthenticationError


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + settings.JWT_ACCESS_TOKEN_EXPIRES

    to_encode.update({"exp": expire, "type": "access"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(data: Dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + settings.JWT_REFRESH_TOKEN_EXPIRES
    to_encode.update({"exp": expire, "type": "refresh"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> Dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except PyJWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


def verify_token(token: str, token_type: str = "access") -> Dict:
    """Verify token and check type"""
    payload = decode_token(token)

    if payload.get("type") != token_type:
        raise AuthenticationError(f"Invalid token type. Expected {token_type}")

    return payload


def get_user_id_from_token(token: str) -> int:
    """Extract user ID from token"""
    payload = verify_token(token, "access")
    user_id = payload.get("sub")

    if not user_id:
        raise AuthenticationError("Invalid token: missing user ID")

    return int(user_id)
