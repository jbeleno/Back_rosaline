"""Repository wrapper for user persistence operations."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from .. import crud, models, schemas
from .base import Repository


class UsuarioRepository(Repository):
    """Wrapper around CRUD helpers focused on usuarios."""

    def __init__(self, session: Session):
        super().__init__(session)

    def get(self, usuario_id: int) -> Optional[models.Usuario]:
        return crud.get_usuario(self.session, usuario_id)

    def get_by_email(self, correo: str) -> Optional[models.Usuario]:
        return crud.get_usuario_por_correo(self.session, correo)

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        rol: Optional[str] = None,
        correo: Optional[str] = None,
        email_verificado: Optional[str] = None,
    ):
        return crud.get_usuarios(
            self.session,
            skip=skip,
            limit=limit,
            rol=rol,
            correo=correo,
            email_verificado=email_verificado,
        )

    def create(self, usuario: schemas.UsuarioCreate) -> models.Usuario:
        return crud.crear_usuario(self.session, usuario)

    def update(
        self,
        usuario_id: int,
        usuario: schemas.UsuarioUpdate,
        es_super_admin: bool = False,
    ) -> Optional[models.Usuario]:
        return crud.actualizar_usuario(
            self.session,
            usuario_id,
            usuario,
            es_super_admin=es_super_admin,
        )

    def delete(self, usuario_id: int) -> Optional[models.Usuario]:
        return crud.eliminar_usuario(self.session, usuario_id)

    def confirm_account(self, correo: str, pin: str) -> models.Usuario:
        return crud.confirmar_cuenta(self.session, correo, pin)

    def regenerate_confirmation_pin(self, correo: str) -> str:
        return crud.regenerar_token_confirmacion(self.session, correo)

    def generate_recovery_pin(self, correo: str) -> str:
        return crud.generar_pin_recuperacion(self.session, correo)

    def validate_recovery_pin(self, correo: str, pin: str) -> bool:
        return crud.validar_pin_recuperacion(self.session, correo, pin)

    def change_password_with_pin(
        self,
        correo: str,
        pin: str,
        nueva_contraseña: str,
    ) -> models.Usuario:
        return crud.cambiar_contraseña_con_pin(self.session, correo, pin, nueva_contraseña)

    def change_password_authenticated(
        self,
        usuario_id: int,
        contraseña_actual: str,
        nueva_contraseña: str,
    ) -> models.Usuario:
        return crud.cambiar_contraseña_usuario(
            self.session,
            usuario_id,
            contraseña_actual,
            nueva_contraseña,
        )
