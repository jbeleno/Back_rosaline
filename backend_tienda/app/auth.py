from datetime import datetime, timedelta
# Name: datetime, timedelta
# Nombre: datetime, timedelta
# Description: Provides classes for manipulating dates and times.
# Descripción: Proporciona clases para manipular fechas y horas.
from jose import JWTError, jwt
# Name: jose (JWTError, jwt)
# Nombre: jose (JWTError, jwt)
# Description: Library for encoding, decoding, and handling JSON Web Tokens (JWT).
# Descripción: Librería para codificar, decodificar y manejar JSON Web Tokens (JWT).
from fastapi import Depends, HTTPException, status
# Name: fastapi (Depends, HTTPException, status)
# Nombre: fastapi (Depends, HTTPException, status)
# Description: FastAPI framework utilities for dependency injection, HTTP exceptions, and status codes.
# Descripción: Utilidades del framework FastAPI para inyección de dependencias, excepciones HTTP y códigos de estado.
from fastapi.security import OAuth2PasswordBearer
# Name: fastapi.security (OAuth2PasswordBearer)
# Nombre: fastapi.security (OAuth2PasswordBearer)
# Description: Provides OAuth2 password flow for authentication in FastAPI.
# Descripción: Proporciona el flujo de autenticación OAuth2 por contraseña en FastAPI.
from passlib.context import CryptContext
# Name: passlib.context (CryptContext)
# Nombre: passlib.context (CryptContext)
# Description: Utility for hashing and verifying passwords securely.
# Descripción: Utilidad para hashear y verificar contraseñas de forma segura.

# Name: Authentication Utilities
# Nombre: Utilidades de Autenticación
# Description: Functions for password hashing, JWT token creation, and user authentication.
# Descripción: Funciones para hashear contraseñas, crear tokens JWT y autenticar usuarios.

# Cambia esta clave por una segura y mantenla en secreto
SECRET_KEY = "cambia_esta_clave_por_una_segura"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def crear_token_de_acceso(data: dict, expires_delta: timedelta = None):
    # Name: Create Access Token
    # Nombre: Crear Token de Acceso
    # Description: Generates a JWT access token with expiration.
    # Descripción: Genera un token de acceso JWT con expiración.
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verificar_token(token: str):
    # Name: Verify Token
    # Nombre: Verificar Token
    # Description: Decodes and validates a JWT token. Returns the payload if valid, otherwise None.
    # Descripción: Decodifica y valida un token JWT. Retorna el payload si es válido, de lo contrario None.
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user(token: str = Depends(oauth2_scheme)):
    # Name: Get Current User
    # Nombre: Obtener Usuario Actual
    # Description: Extracts user information from the JWT token. Raises an exception if invalid or expired.
    # Descripción: Extrae la información del usuario desde el token JWT. Lanza una excepción si es inválido o expirado.
    payload = verificar_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

def hash_password(password: str) -> str:
    # Name: Hash Password
    # Nombre: Hashear Contraseña
    # Description: Hashes a plain password using bcrypt.
    # Descripción: Hashea una contraseña en texto plano usando bcrypt.
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Name: Verify Password
    # Nombre: Verificar Contraseña
    # Description: Checks if a plain password matches the hashed password.
    # Descripción: Verifica si una contraseña en texto plano coincide con la contraseña hasheada.
    return pwd_context.verify(plain_password, hashed_password) 