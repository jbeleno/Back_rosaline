"""Repository wrapper for Cliente persistence operations."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from .. import crud, models, schemas
from .base import Repository


class ClienteRepository(Repository):
    """Repository utility for clientes."""

    def __init__(self, session: Session):
        super().__init__(session)

    def list(self, skip: int = 0, limit: int = 100):
        return crud.get_clientes(self.session, skip=skip, limit=limit)

    def create(self, cliente: schemas.ClienteCreate) -> models.Cliente:
        return crud.crear_cliente(self.session, cliente)

    def get(self, cliente_id: int) -> Optional[models.Cliente]:
        return crud.get_cliente(self.session, cliente_id)

    def get_by_usuario(self, id_usuario: int) -> Optional[models.Cliente]:
        return crud.get_cliente_por_id_usuario(self.session, id_usuario)

    def update(self, cliente_id: int, cliente: schemas.ClienteCreate) -> Optional[models.Cliente]:
        return crud.actualizar_cliente(self.session, cliente_id, cliente)

    def delete(self, cliente_id: int) -> Optional[models.Cliente]:
        return crud.eliminar_cliente(self.session, cliente_id)
