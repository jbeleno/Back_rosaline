"""Repository wrapper for DetallePedido persistence operations."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from .. import crud, models, schemas
from .base import Repository


class DetallePedidoRepository(Repository):
    def __init__(self, session: Session):
        super().__init__(session)

    def list(self, skip: int = 0, limit: int = 100):
        return crud.get_detalles_pedido(self.session, skip=skip, limit=limit)

    def create(self, detalle: schemas.DetallePedidoCreate) -> models.DetallePedido:
        return crud.crear_detalle_pedido(self.session, detalle)

    def get(self, detalle_id: int) -> Optional[models.DetallePedido]:
        return crud.get_detalle_pedido(self.session, detalle_id)

    def update(self, detalle_id: int, detalle: schemas.DetallePedidoCreate) -> Optional[models.DetallePedido]:
        return crud.actualizar_detalle_pedido(self.session, detalle_id, detalle)

    def delete(self, detalle_id: int) -> Optional[models.DetallePedido]:
        return crud.eliminar_detalle_pedido(self.session, detalle_id)
