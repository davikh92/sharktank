from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
import jwt
import bcrypt
import os
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_MINUTES = int(os.environ.get('JWT_EXPIRATION_MINUTES', '43200'))
APP_ENV = os.environ.get('APP_ENV', 'development').strip().lower()

logger = logging.getLogger(__name__)


def _resolve_jwt_secret() -> str:
    configured_secret = os.environ.get('JWT_SECRET')

    # Em produção/staging, nunca aceitar fallback inseguro.
    if APP_ENV in {'production', 'staging'}:
        if not configured_secret:
            raise RuntimeError(
                'JWT_SECRET é obrigatório quando APP_ENV é production/staging.'
            )
        return configured_secret

    # Em desenvolvimento/local, manter fallback para não quebrar fluxos existentes
    # (incluindo ambientes gerenciados que não setam segredo explicitamente).
    if not configured_secret:
        logger.warning(
            'JWT_SECRET não configurado; usando fallback apenas para ambiente %s.',
            APP_ENV,
        )
        return 'fallback-secret'

    return configured_secret


JWT_SECRET = _resolve_jwt_secret()

security = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRATION_MINUTES)

    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token expirado'
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token inválido'
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = decode_access_token(token)
    return payload
