"""Repository wrapper for Pedido persistence operations."""

from __future__ import annotations

from typing import Optional, List

from sqlalchemy.orm import Session

from .. import crud, models, schemas
from .base import Repository


class PedidoRepository(Repository):
    def __init__(self, session: Session):
        super().__init__(session)

    def list(self, skip: int = 0, limit: int = 100) -> List[models.Pedido]:
        return crud.get_pedidos(self.session, skip=skip, limit=limit)

    def create(self, pedido: schemas.PedidoCreate) -> models.Pedido:
        return crud.crear_pedido(self.session, pedido)

    def get(self, pedido_id: int) -> Optional[models.Pedido]:
        return crud.get_pedido(self.session, pedido_id)

    def update(self, pedido_id: int, pedido: schemas.PedidoCreate) -> Optional[models.Pedido]:
        return crud.actualizar_pedido(self.session, pedido_id, pedido)

    def delete(self, pedido_id: int) -> Optional[models.Pedido]:
        return crud.eliminar_pedido(self.session, pedido_id)

    def get_by_cliente_id(self, cliente_id: int, skip: int = 0, limit: int = 100) -> List[models.Pedido]:
        return self.session.query(models.Pedido).filter(models.Pedido.id_cliente == cliente_id).offset(skip).limit(limit).all()

    def get_by_estado(self, estado: str, skip: int = 0, limit: int = 100) -> List[models.Pedido]:
        return self.session.query(models.Pedido).filter(models.Pedido.estado == estado).offset(skip).limit(limit).all()

    def get_by_estado_and_cliente_ids(self, estado: str, cliente_ids: List[int], skip: int = 0, limit: int = 100) -> List[models.Pedido]:
        return self.session.query(models.Pedido).filter(models.Pedido.estado == estado, models.Pedido.id_cliente.in_(cliente_ids)).offset(skip).limit(limit).all()

    def list_by_cliente_ids(self, cliente_ids: List[int], skip: int = 0, limit: int = 100) -> List[models.Pedido]:
        return self.session.query(models.Pedido).filter(models.Pedido.id_cliente.in_(cliente_ids)).offset(skip).limit(limit).all()
