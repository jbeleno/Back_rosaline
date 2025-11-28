"""
Tests para el sistema de notificaciones, como el envío de correos.

Cubre casos de prueba:
- CP-019: Generación de email de confirmación de cuenta
"""

import pytest
from unittest.mock import MagicMock

from tests.conftest import get_auth_headers

def test_registro_envia_email_confirmacion(client, monkeypatch):
    """
    CP-019: Verifica que al registrar un nuevo usuario, se intenta enviar
    un correo electrónico de confirmación.
    """
    # 1. Crear un mock para el servicio de email
    mock_email_service = MagicMock()
    
    # 2. Usar monkeypatch para reemplazar el servicio real por nuestro mock
    # Esto interceptará cualquier llamada al servicio de email
    monkeypatch.setattr("app.services.usuario_service.email_service", mock_email_service)

    # 3. Registrar un nuevo usuario
    correo_nuevo_usuario = "nuevo_usuario_email@example.com"
    response = client.post(
        "/usuarios/",
        json={
            "correo": correo_nuevo_usuario,
            "contraseña": "passwordValido123",
            "rol": "cliente"
        }
    )
    assert response.status_code == 201
    nuevo_usuario = response.json()

    # 4. Verificar que la función de enviar email fue llamada exactamente una vez
    mock_email_service.enviar_email_confirmacion.assert_called_once()

    # 5. (Opcional pero recomendado) Verificar que fue llamada con los argumentos correctos
    # Se inspeccionan los kwargs (keyword arguments) ya que el servicio puede ser llamado con ellos
    call_args, call_kwargs = mock_email_service.enviar_email_confirmacion.call_args
    
    # Verificar que los argumentos correctos ('destinatario' y 'pin') están en los kwargs
    assert "destinatario" in call_kwargs
    assert call_kwargs["destinatario"] == correo_nuevo_usuario
    
    assert "pin" in call_kwargs
    pin_arg = call_kwargs["pin"]
    assert isinstance(pin_arg, str)
    assert len(pin_arg) >= 4 # Asumiendo un PIN de al menos 4 dígitos
