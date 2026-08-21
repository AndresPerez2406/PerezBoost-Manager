from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.core.config import settings

security_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Genera un hash seguro bcrypt para una contraseña."""
    if not password:
        password = "1234"
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña coincide con el hash (o con texto plano legado)."""
    if not hashed_password or not plain_password:
        return False
    if not hashed_password.startswith("$2b$") and not hashed_password.startswith("$2a$"):
        # Contraseña legada en texto plano
        return plain_password == hashed_password
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Genera un token JWT firmado criptográficamente."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica y valida un token JWT."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

# =============================================================================
# DEPENDENCIAS DE AUTENTICACIÓN Y ROLES (RBAC)
# =============================================================================

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)) -> dict:
    """Valida el token Bearer y retorna el usuario autenticado."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Exige rol de Administrador. Lanza HTTP 403 si es un usuario estándar."""
    role = current_user.get("role")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido: Se requieren permisos de Administrador."
        )
    return current_user

def require_booster_or_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Permite el acceso a Boosters autenticados y Administradores."""
    role = current_user.get("role")
    if role not in ["admin", "booster"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido: Rol no autorizado."
        )
    return current_user
