"""Módulo de envío de correos electrónicos para el backend."""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from .core.config import get_settings

settings = get_settings()

class EmailService:
    """Servicio para el envío de correos electrónicos transaccionales."""

    def __init__(self):
        # Cargar configuración desde el objeto centralizado de Settings
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from_email = settings.SMTP_FROM_EMAIL
        self.smtp_from_name = settings.SMTP_FROM_NAME or settings.PROJECT_NAME
        self.frontend_url = settings.FRONTEND_URL

        if not all([self.smtp_host, self.smtp_port, self.smtp_user, self.smtp_password, self.smtp_from_email]):
            raise ValueError("La configuración de SMTP no está completa. Revisa las variables de entorno.")

    def send_email(
        self,
        destinatario: str,
        asunto: str,
        cuerpo_html: str,
        cuerpo_texto: Optional[str] = None,
    ) -> bool:
        """Envía un correo electrónico con cuerpo en HTML y texto plano."""

        if not self.smtp_user or not self.smtp_password:
            print(f"⚠️  SMTP no configurado. No se puede enviar email a {destinatario}")
            return False

        try:
            mensaje = MIMEMultipart("alternative")
            mensaje["Subject"] = asunto
            mensaje["From"] = f"{self.smtp_from_name} <{self.smtp_from_email}>"
            mensaje["To"] = destinatario

            if cuerpo_texto:
                parte_texto = MIMEText(cuerpo_texto, "plain", "utf-8")
                mensaje.attach(parte_texto)

            parte_html = MIMEText(cuerpo_html, "html", "utf-8")
            mensaje.attach(parte_html)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as servidor:
                servidor.starttls()
                servidor.login(self.smtp_user, self.smtp_password)
                servidor.send_message(mensaje)

            print(f"✅ Email enviado a {destinatario}")
            return True

        except Exception as exc:  # pragma: no cover - logging side effect
            print(f"❌ Error al enviar email a {destinatario}: {exc}")
            return False

    def send_confirmation_email(self, destinatario: str, nombre: str, pin: str) -> bool:
        """Envía email de confirmación de cuenta con PIN."""

        asunto = "Confirma tu cuenta - Rosaline Bakery"
        cuerpo_html = self._build_confirmation_html(nombre, pin)
        cuerpo_texto = self._build_confirmation_text(nombre, pin)
        return self.send_email(destinatario, asunto, cuerpo_html, cuerpo_texto)

    def send_recovery_email(self, destinatario: str, nombre: str, pin: str) -> bool:
        """Envía email con PIN de recuperación de contraseña."""

        asunto = "Recuperación de contraseña - Rosaline Bakery"
        cuerpo_html = self._build_recovery_html(nombre, pin)
        cuerpo_texto = self._build_recovery_text(nombre, pin)
        return self.send_email(destinatario, asunto, cuerpo_html, cuerpo_texto)

    @staticmethod
    def _build_confirmation_html(nombre: str, pin: str) -> str:
        return f"""
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

    @staticmethod
    def _build_confirmation_text(nombre: str, pin: str) -> str:
        return f"""
        ¡Bienvenido, {nombre}!

        Gracias por registrarte en Rosaline Bakery. Para completar tu registro, ingresa el siguiente PIN de confirmación en la página de registro:

        PIN: {pin}

        Este PIN expirará en 15 minutos. Si no lo usas a tiempo, puedes solicitar uno nuevo.

        Ingresa este PIN en la página donde te registraste para confirmar tu cuenta.

        Si no creaste esta cuenta, puedes ignorar este correo.

        © 2025 Rosaline Bakery. Todos los derechos reservados.
        """

    @staticmethod
    def _build_recovery_html(nombre: str, pin: str) -> str:
        return f"""
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
                        <strong>⚠️ Importante:</strong> Este PIN expirará en 15 minutos. Si no solicitaste este cambio, ignora este correo.</div>
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

    @staticmethod
    def _build_recovery_text(nombre: str, pin: str) -> str:
        return f"""
        Hola, {nombre}

        Recibimos una solicitud para restablecer la contraseña de tu cuenta. Usa el siguiente PIN para continuar:

        PIN: {pin}

        ⚠️ IMPORTANTE: Este PIN expirará en 15 minutos. Si no solicitaste este cambio, ignora este correo.

        Ingresa este PIN en la página de recuperación de contraseña para continuar.

        © 2025 Rosaline Bakery. Todos los derechos reservados.
        Por seguridad, nunca compartas este PIN con nadie.
        """


_default_email_service = EmailService()


def enviar_email(destinatario: str, asunto: str, cuerpo_html: str, cuerpo_texto: Optional[str] = None) -> bool:
    """Compatibilidad con la API previa basada en funciones."""

    return _default_email_service.send_email(destinatario, asunto, cuerpo_html, cuerpo_texto)


def enviar_email_confirmacion(destinatario: str, nombre: str, pin: str) -> bool:
    """Compatibilidad con la API previa basada en funciones."""

    return _default_email_service.send_confirmation_email(destinatario, nombre, pin)


def enviar_email_recuperacion(destinatario: str, nombre: str, pin: str) -> bool:
    """Compatibilidad con la API previa basada en funciones."""

    return _default_email_service.send_recovery_email(destinatario, nombre, pin)

