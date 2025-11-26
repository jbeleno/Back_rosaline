"""Repository wrapper for Pedido persistence operations."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from .. import crud, models, schemas
from .base import Repository


class PedidoRepository(Repository):
    def __init__(self, session: Session):
        super().__init__(session)

    def list(self, skip: int = 0, limit: int = 100):
        return crud.get_pedidos(self.session, skip=skip, limit=limit)

    def create(self, pedido: schemas.PedidoCreate) -> models.Pedido:
        return crud.crear_pedido(self.session, pedido)

    def get(self, pedido_id: int) -> Optional[models.Pedido]:
        return crud.get_pedido(self.session, pedido_id)

    def update(self, pedido_id: int, pedido: schemas.PedidoCreate) -> Optional[models.Pedido]:
        return crud.actualizar_pedido(self.session, pedido_id, pedido)

    def delete(self, pedido_id: int) -> Optional[models.Pedido]:
        return crud.eliminar_pedido(self.session, pedido_id)
