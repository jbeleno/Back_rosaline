"""Repository wrapper for Cliente persistence operations."""

from __future__ import annotations

from typing import Optional, List

from sqlalchemy.orm import Session, joinedload

from .. import crud, models, schemas
from .base import Repository


class ClienteRepository(Repository):
    """Repository utility for clientes."""

    def __init__(self, session: Session):
        super().__init__(session)

    def get_by_id(self, cliente_id: int) -> Optional[models.Cliente]:
        return self.session.query(models.Cliente).options(joinedload(models.Cliente.usuario)).filter(models.Cliente.id_cliente == cliente_id).first()

    def get_by_usuario_id(self, usuario_id: int) -> Optional[models.Cliente]:
        return self.session.query(models.Cliente).options(joinedload(models.Cliente.usuario)).filter(models.Cliente.id_usuario == usuario_id).first()

    def list(self, skip: int = 0, limit: int = 100) -> List[models.Cliente]:
        return self.session.query(models.Cliente).options(joinedload(models.Cliente.usuario)).offset(skip).limit(limit).all()

    def create(self, cliente: schemas.ClienteCreate, usuario_id: int) -> models.Cliente:
        return crud.crear_cliente(self.session, cliente)

    def get(self, cliente_id: int) -> Optional[models.Cliente]:
        return crud.get_cliente(self.session, cliente_id)

    def get_by_usuario(self, id_usuario: int) -> Optional[models.Cliente]:
        return crud.get_cliente_por_id_usuario(self.session, id_usuario)

    def update(self, cliente_id: int, cliente: schemas.ClienteCreate) -> Optional[models.Cliente]:
        return crud.actualizar_cliente(self.session, cliente_id, cliente)

    def delete(self, cliente_id: int) -> Optional[models.Cliente]:
        return crud.eliminar_cliente(self.session, cliente_id)
