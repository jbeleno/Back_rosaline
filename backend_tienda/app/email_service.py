"""
Módulo para envío de correos electrónicos.

Incluye funciones para:
- Enviar email de confirmación de cuenta
- Enviar PIN de recuperación de contraseña

Dependencias:
- smtplib (estándar de Python)
- email (estándar de Python)
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Configuración SMTP desde variables de entorno
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")  # Email del remitente
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # Clave de aplicación
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Rosaline Bakery")

# URL base del frontend para links
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://rosalinebakery.me")


def enviar_email(
    destinatario: str,
    asunto: str,
    cuerpo_html: str,
    cuerpo_texto: Optional[str] = None
) -> bool:
    """
    Envía un correo electrónico.
    
    Args:
        destinatario: Email del destinatario
        asunto: Asunto del correo
        cuerpo_html: Cuerpo del correo en HTML
        cuerpo_texto: Cuerpo del correo en texto plano (opcional)
    
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"⚠️  SMTP no configurado. No se puede enviar email a {destinatario}")
        return False
    
    try:
        # Crear mensaje
        mensaje = MIMEMultipart("alternative")
        mensaje["Subject"] = asunto
        mensaje["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        mensaje["To"] = destinatario
        
        # Agregar cuerpo en texto plano si se proporciona
        if cuerpo_texto:
            parte_texto = MIMEText(cuerpo_texto, "plain", "utf-8")
            mensaje.attach(parte_texto)
        
        # Agregar cuerpo en HTML
        parte_html = MIMEText(cuerpo_html, "html", "utf-8")
        mensaje.attach(parte_html)
        
        # Enviar email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
            servidor.starttls()
            servidor.login(SMTP_USER, SMTP_PASSWORD)
            servidor.send_message(mensaje)
        
        print(f"✅ Email enviado a {destinatario}")
        return True
    
    except Exception as e:
        print(f"❌ Error al enviar email a {destinatario}: {e}")
        return False


def enviar_email_confirmacion(destinatario: str, nombre: str, pin: str) -> bool:
    """
    Envía email de confirmación de cuenta con PIN.
    
    Args:
        destinatario: Email del destinatario
        nombre: Nombre del usuario
        pin: PIN de 6 dígitos para confirmar la cuenta
    
    Returns:
        bool: True si se envió correctamente
    """
    asunto = "Confirma tu cuenta - Rosaline Bakery"
    
    cuerpo_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #d4a574; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .pin-box {{ background-color: #fff; border: 2px solid #d4a574; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0; }}
            .pin {{ font-size: 32px; font-weight: bold; color: #d4a574; letter-spacing: 8px; font-family: 'Courier New', monospace; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            .warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🍪 Rosaline Bakery</h1>
            </div>
            <div class="content">
                <h2>¡Bienvenido, {nombre}!</h2>
                <p>Gracias por registrarte en Rosaline Bakery. Para completar tu registro, ingresa el siguiente PIN de confirmación en la página de registro:</p>
                <div class="pin-box">
                    <p style="margin: 0 0 10px 0; color: #666;">Tu PIN de confirmación:</p>
                    <div class="pin">{pin}</div>
                </div>
                <div class="warning">
                    <strong>⚠️ Importante:</strong> Este PIN expirará en 15 minutos. Si no lo usas a tiempo, puedes solicitar uno nuevo.
                </div>
                <p>Ingresa este PIN en la página donde te registraste para confirmar tu cuenta.</p>
                <p>Si no creaste esta cuenta, puedes ignorar este correo.</p>
            </div>
            <div class="footer">
                <p>© 2025 Rosaline Bakery. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    cuerpo_texto = f"""
    ¡Bienvenido, {nombre}!
    
    Gracias por registrarte en Rosaline Bakery. Para completar tu registro, ingresa el siguiente PIN de confirmación en la página de registro:
    
    PIN: {pin}
    
    Este PIN expirará en 15 minutos. Si no lo usas a tiempo, puedes solicitar uno nuevo.
    
    Ingresa este PIN en la página donde te registraste para confirmar tu cuenta.
    
    Si no creaste esta cuenta, puedes ignorar este correo.
    
    © 2025 Rosaline Bakery. Todos los derechos reservados.
    """
    
    return enviar_email(destinatario, asunto, cuerpo_html, cuerpo_texto)


def enviar_email_recuperacion(destinatario: str, nombre: str, pin: str) -> bool:
    """
    Envía email con PIN de recuperación de contraseña.
    
    Args:
        destinatario: Email del destinatario
        nombre: Nombre del usuario
        pin: PIN de 6 dígitos
    
    Returns:
        bool: True si se envió correctamente
    """
    asunto = "Recuperación de contraseña - Rosaline Bakery"
    
    cuerpo_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #d4a574; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .pin-box {{ background-color: #fff; border: 2px solid #d4a574; padding: 20px; text-align: center; margin: 20px 0; border-radius: 5px; }}
            .pin {{ font-size: 32px; font-weight: bold; color: #d4a574; letter-spacing: 10px; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            .warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Recuperación de Contraseña</h1>
            </div>
            <div class="content">
                <h2>Hola, {nombre}</h2>
                <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta. Usa el siguiente PIN para continuar:</p>
                <div class="pin-box">
                    <div class="pin">{pin}</div>
                </div>
                <div class="warning">
                    <strong>⚠️ Importante:</strong> Este PIN expirará en 15 minutos. Si no solicitaste este cambio, ignora este correo.
                </div>
                <p>Ingresa este PIN en la página de recuperación de contraseña para continuar.</p>
            </div>
            <div class="footer">
                <p>© 2025 Rosaline Bakery. Todos los derechos reservados.</p>
                <p>Por seguridad, nunca compartas este PIN con nadie.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    cuerpo_texto = f"""
    Hola, {nombre}
    
    Recibimos una solicitud para restablecer la contraseña de tu cuenta. Usa el siguiente PIN para continuar:
    
    PIN: {pin}
    
    ⚠️ IMPORTANTE: Este PIN expirará en 15 minutos. Si no solicitaste este cambio, ignora este correo.
    
    Ingresa este PIN en la página de recuperación de contraseña para continuar.
    
    © 2025 Rosaline Bakery. Todos los derechos reservados.
    Por seguridad, nunca compartas este PIN con nadie.
    """
    
    return enviar_email(destinatario, asunto, cuerpo_html, cuerpo_texto)

