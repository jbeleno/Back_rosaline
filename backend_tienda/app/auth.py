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

from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext


# Cambia esta clave por una segura y mantenla en secreto
SECRET_KEY = "cambia_esta_clave_por_una_segura"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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