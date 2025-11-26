"""Repository wrapper for DetallePedido persistence operations."""

from __future__ import annotations

from typing import Optional, List

from sqlalchemy.orm import Session

from .. import crud, models, schemas
from .base import Repository


class DetallePedidoRepository(Repository):
    def __init__(self, session: Session):
        super().__init__(session)

    def get_by_pedido_id(self, pedido_id: int, skip: int = 0, limit: int = 100) -> List[models.DetallePedido]:
        return self.session.query(models.DetallePedido).filter(models.DetallePedido.id_pedido == pedido_id).offset(skip).limit(limit).all()

    def get_productos_by_pedido_id(self, pedido_id: int) -> List[models.Producto]:
        return self.session.query(models.Producto).join(models.DetallePedido).filter(models.DetallePedido.id_pedido == pedido_id).all()
        
    def list(self, skip: int = 0, limit: int = 100, pedido_id: Optional[int] = None) -> List[models.DetallePedido]:
        query = self.session.query(models.DetallePedido).options(
            self.session.query(models.Producto).join(models.DetallePedido).filter(models.DetallePedido.id_pedido == pedido_id).all()
        )
        return query.offset(skip).limit(limit).all()

    def create(self, detalle: schemas.DetallePedidoCreate) -> models.DetallePedido:
        return crud.crear_detalle_pedido(self.session, detalle)

    def get(self, detalle_id: int) -> Optional[models.DetallePedido]:
        return crud.get_detalle_pedido(self.session, detalle_id)

    def update(self, detalle_id: int, detalle: schemas.DetallePedidoCreate) -> Optional[models.DetallePedido]:
        return crud.actualizar_detalle_pedido(self.session, detalle_id, detalle)

    def delete(self, detalle_id: int) -> Optional[models.DetallePedido]:
        return crud.eliminar_detalle_pedido(self.session, detalle_id)
