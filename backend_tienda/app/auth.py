"""
Authentication utilities module for the API.
"""

from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from .core.config import get_settings

settings = get_settings()

# Constants moved to centralized settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Configurar CryptContext con bcrypt, deshabilitando la detección automática de bugs
# que puede causar problemas con algunas versiones de bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


def crear_token_de_acceso(data: dict, expires_delta: timedelta = None):
    """
    Generates a JWT access token with expiration.

    Args:
        data (dict): Data to encode in the token.
        expires_delta (timedelta, optional): Token expiration time.

    Returns:
        str: Encoded JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verificar_token(token: str):
    """
    Decodes and validates a JWT token.

    Args:
        token (str): JWT token to verify.

    Returns:
        dict | None: Payload if valid, None if invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Extracts user information from the JWT token.
    Raises an HTTP exception if the token is invalid or expired.

    Args:
        token (str): JWT token extracted from the request.

    Returns:
        dict: Payload of the authenticated user.
    """
    payload = verificar_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_role(required_roles: list[str]):
    """
    Dependency factory that validates the user has one of the required roles.
    
    Args:
        required_roles: List of allowed roles (e.g., ["admin"], ["cliente"], ["admin", "cliente"])
    
    Returns:
        function: Dependency function that validates the role
    """
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("rol")
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere uno de los roles: {required_roles}"
            )
        return current_user
    return role_checker


def require_admin():
    """Dependency that validates the user is an administrator or super administrator."""
    return require_role(["admin", "super_admin"])


def require_super_admin():
    """Dependency that validates the user is a super administrator."""
    return require_role(["super_admin"])


def require_cliente():
    """Dependency that validates the user is a client."""
    return require_role(["cliente"])


def require_cliente_or_admin():
    """Dependency that validates the user is a client, administrator or super administrator."""
    return require_role(["cliente", "admin", "super_admin"])


def verify_resource_owner(resource_user_id: int, current_user: dict = Depends(get_current_user)):
    """
    Validates that the user is the owner of the resource or is an administrator/super administrator.
    
    Args:
        resource_user_id: ID of the user who owns the resource
        current_user: Current authenticated user
    
    Returns:
        dict: Authenticated user if they have permissions
    
    Raises:
        HTTPException: If the user doesn't have permissions
    """
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    if user_role not in ["admin", "super_admin"] and user_id != resource_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a este recurso"
        )
    return current_user


def hash_password(password: str) -> str:
    """
    Hashes a plain text password using bcrypt.

    Args:
        password (str): Plain text password.

    Returns:
        str: Hashed password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain text password matches the hashed password.

    Args:
        plain_password (str): Plain text password.
        hashed_password (str): Hashed password.

    Returns:
        bool: True if they match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


class AuthService:
    """Servicio de apoyo para operaciones de autenticación y seguridad."""

    def __init__(self):
        self._secret_key = SECRET_KEY
        self._algorithm = ALGORITHM
        self._access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES

    def hash_password(self, password: str) -> str:
        return hash_password(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        return crear_token_de_acceso(data, expires_delta)

    def decode_token(self, token: str) -> dict | None:
        return verificar_token(token)

    @property
    def access_token_expire_minutes(self) -> int:
        return self._access_token_expire_minutes