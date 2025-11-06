"""
Authentication utilities module for the API.

Includes functions for:
- Hashing and verifying passwords.
- Creating and validating JWT tokens.
- Retrieving the current authenticated user.

Main dependencies:
- FastAPI
- jose
- passlib
"""

import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Leer SECRET_KEY desde variable de entorno, con fallback para desarrollo
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY no está configurada. Por favor, configura la variable de entorno SECRET_KEY."
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

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
    """Dependency that validates the user is an administrator."""
    return require_role(["admin"])

def require_cliente():
    """Dependency that validates the user is a client."""
    return require_role(["cliente"])

def require_cliente_or_admin():
    """Dependency that validates the user is a client or administrator."""
    return require_role(["cliente", "admin"])

def verify_resource_owner(resource_user_id: int, current_user: dict = Depends(get_current_user)):
    """
    Validates that the user is the owner of the resource or is an administrator.
    
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
    
    if user_role != "admin" and user_id != resource_user_id:
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