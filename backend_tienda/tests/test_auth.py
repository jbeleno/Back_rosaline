"""
Tests unitarios para el módulo de autenticación (auth.py).

Prueba las funciones de hash de contraseñas, creación y verificación de tokens JWT.
"""

import pytest
from datetime import timedelta
from app.auth import (
    hash_password,
    verify_password,
    crear_token_de_acceso,
    verificar_token,
)


class TestPasswordHashing:
    """Pruebas para el hash y verificación de contraseñas."""
    
    def test_hash_password(self):
        """Prueba que hash_password genera un hash diferente al texto plano."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)
    
    def test_hash_password_different_results(self):
        """Prueba que cada hash es único (incluye salt)."""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Los hashes deben ser diferentes debido al salt
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Prueba que verify_password valida correctamente una contraseña correcta."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Prueba que verify_password rechaza una contraseña incorrecta."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False


class TestTokenCreation:
    """Pruebas para la creación y verificación de tokens JWT."""
    
    def test_crear_token_de_acceso(self):
        """Prueba que crear_token_de_acceso genera un token válido."""
        data = {"sub": "test@example.com", "id_usuario": 1, "rol": "cliente"}
        token = crear_token_de_acceso(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_crear_token_con_expiración_personalizada(self):
        """Prueba que se puede crear un token con expiración personalizada."""
        data = {"sub": "test@example.com", "id_usuario": 1, "rol": "cliente"}
        expires_delta = timedelta(minutes=30)
        token = crear_token_de_acceso(data, expires_delta=expires_delta)
        
        assert token is not None
    
    def test_verificar_token_valido(self):
        """Prueba que verificar_token valida correctamente un token válido."""
        data = {"sub": "test@example.com", "id_usuario": 1, "rol": "cliente"}
        token = crear_token_de_acceso(data)
        
        payload = verificar_token(token)
        
        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert payload["id_usuario"] == 1
        assert payload["rol"] == "cliente"
        assert "exp" in payload
    
    def test_verificar_token_invalido(self):
        """Prueba que verificar_token rechaza un token inválido."""
        invalid_token = "invalid_token_string"
        
        payload = verificar_token(invalid_token)
        
        assert payload is None
    
    def test_verificar_token_con_datos_adicionales(self):
        """Prueba que el token incluye todos los datos proporcionados."""
        data = {
            "sub": "test@example.com",
            "id_usuario": 1,
            "rol": "admin",
            "extra_data": "test"
        }
        token = crear_token_de_acceso(data)
        
        payload = verificar_token(token)
        
        assert payload["sub"] == "test@example.com"
        assert payload["id_usuario"] == 1
        assert payload["rol"] == "admin"
        assert payload["extra_data"] == "test"
