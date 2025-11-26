"""Service layer for user-related business logic."""
from fastapi import HTTPException, status
from ..repositories.usuario_repository import UsuarioRepository
from .. import schemas, email_service, models
from ..auth import verify_password, create_access_token
from typing import Optional

class UsuarioService:
    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository

    def autenticar_usuario(self, correo: str, contraseña: str) -> Optional[models.Usuario]:
        db_usuario = self.usuario_repository.get_by_email(correo)
        if not db_usuario:
            return None
        if not verify_password(contraseña, db_usuario.contraseña_hash):
            return None
        if db_usuario.email_verificado != "S":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cuenta no confirmada. Por favor, verifica tu correo electrónico."
            )
        return db_usuario
        
    def crear_usuario(self, usuario: schemas.UsuarioCreate):
        db_usuario = self.usuario_repository.get_by_email(correo=usuario.correo)
        if db_usuario:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Correo ya registrado")

        nuevo_usuario = self.usuario_repository.create(usuario=usuario)
        
        # Lógica de envío de email
        nombre = usuario.correo.split("@")[0]
        email_service.enviar_email_confirmacion(
            destinatario=nuevo_usuario.correo,
            nombre=nombre,
            pin=nuevo_usuario.token_confirmacion
        )
        return nuevo_usuario

    def confirmar_cuenta(self, correo: str, pin: str):
        return self.usuario_repository.confirm_account(correo, pin)

    def reenviar_confirmacion(self, correo: str):
        nuevo_pin = self.usuario_repository.regenerate_confirmation_pin(correo)
        usuario = self.usuario_repository.get_by_email(correo)
        nombre = correo.split("@")[0]
        # Aquí podrías buscar el perfil del cliente para un nombre más amigable si existe
        email_service.enviar_email_confirmacion(
            destinatario=correo,
            nombre=nombre,
            pin=nuevo_pin
        )
        return {"mensaje": "PIN de confirmación reenviado. Revisa tu bandeja de entrada."}

    def solicitar_recuperacion(self, correo: str):
        try:
            pin = self.usuario_repository.generate_recovery_pin(correo)
            usuario = self.usuario_repository.get_by_email(correo)
            nombre = correo.split("@")[0]
            email_service.enviar_email_recuperacion(
                destinatario=correo,
                nombre=nombre,
                pin=pin
            )
            return {"mensaje": "Se ha enviado un PIN de recuperación a tu correo. Revisa tu bandeja de entrada."}
        except HTTPException:
            return {"mensaje": "Si el correo existe, se ha enviado un PIN de recuperación."}

    def validar_pin_recuperacion(self, correo: str, pin: str):
        es_valido = self.usuario_repository.validate_recovery_pin(correo, pin)
        if es_valido:
            return {"valido": True, "mensaje": "PIN válido. Puedes proceder a cambiar tu contraseña."}
        else:
            return {"valido": False, "mensaje": "PIN inválido o expirado. Solicita un nuevo PIN."}

    def cambiar_contraseña_con_pin(self, request: schemas.CambiarContraseñaRequest):
        self.usuario_repository.change_password_with_pin(
            request.correo,
            request.pin,
            request.nueva_contraseña
        )
        return {"mensaje": "Contraseña cambiada exitosamente. Ya puedes iniciar sesión con tu nueva contraseña."}

    def cambiar_contraseña_autenticado(self, usuario_id: int, request: schemas.CambiarContraseñaAutenticadoRequest):
        self.usuario_repository.change_password_authenticated(
            usuario_id,
            request.contraseña_actual,
            request.nueva_contraseña
        )
        return {"mensaje": "Contraseña cambiada exitosamente."}

    def listar_usuarios(self, skip: int, limit: int, rol: str, correo: str, email_verificado: str):
        return self.usuario_repository.list(skip, limit, rol, correo, email_verificado)

    def obtener_usuario(self, usuario_id: int):
        usuario = self.usuario_repository.get(usuario_id)
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return usuario

    def actualizar_usuario(self, usuario_id: int, usuario_update: schemas.UsuarioUpdate, current_user: dict):
        db_usuario = self.obtener_usuario(usuario_id) # Reutiliza el método para obtener y validar que existe
        
        current_user_id = current_user.get("id_usuario")
        current_user_role = current_user.get("rol")
        es_super_admin = current_user_role == "super_admin"

        if not es_super_admin and usuario_update.email_verificado is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los super administradores pueden modificar el estado de verificación de email"
            )

        if es_super_admin:
            if usuario_id == current_user_id and usuario_update.rol is not None and usuario_update.rol != "super_admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No puedes cambiar tu propio rol. Los super administradores deben mantener su rol."
                )
        elif current_user_role == "admin":
            if db_usuario.rol in ["admin", "super_admin"] and db_usuario.id_usuario != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No puedes modificar a otro administrador o super administrador."
                )

        return self.usuario_repository.update(usuario_id, usuario_update, es_super_admin)

    def eliminar_usuario(self, usuario_id: int, current_user: dict):
        db_usuario = self.obtener_usuario(usuario_id)

        current_user_id = current_user.get("id_usuario")
        current_user_role = current_user.get("rol")

        if usuario_id == current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes eliminarte a ti mismo")

        if current_user_role == "admin":
            if db_usuario.rol in ["admin", "super_admin"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No puedes eliminar a otro administrador o super administrador."
                )
        
        return self.usuario_repository.delete(usuario_id)
