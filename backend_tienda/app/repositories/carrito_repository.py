"""Repository wrapper for Carrito persistence operations."""

from __future__ import annotations

from typing import Optional, List

from sqlalchemy.orm import Session, joinedload

from .. import crud, models, schemas
from .base import Repository


class CarritoRepository(Repository):
    def __init__(self, session: Session):
        super().__init__(session)

    def get_by_id(self, carrito_id: int) -> Optional[models.Carrito]:
        return self.session.query(models.Carrito).options(joinedload(models.Carrito.cliente)).filter(models.Carrito.id_carrito == carrito_id).first()

    def get_by_cliente_id(self, cliente_id: int, skip: int = 0, limit: int = 100) -> List[models.Carrito]:
        return self.session.query(models.Carrito).filter(models.Carrito.id_cliente == cliente_id).offset(skip).limit(limit).all()

    def list_by_cliente_ids(self, cliente_ids: List[int], skip: int = 0, limit: int = 100) -> List[models.Carrito]:
        return self.session.query(models.Carrito).filter(models.Carrito.id_cliente.in_(cliente_ids)).offset(skip).limit(limit).all()
        
    def list(self, skip: int = 0, limit: int = 100) -> List[models.Carrito]:
        return self.session.query(models.Carrito).options(joinedload(models.Carrito.cliente)).offset(skip).limit(limit).all()

    def create(self, carrito: schemas.CarritoCreate) -> models.Carrito:
        return crud.crear_carrito(self.session, carrito)

    def get(self, carrito_id: int) -> Optional[models.Carrito]:
        return crud.get_carrito(self.session, carrito_id)

    def update(self, carrito_id: int, carrito: schemas.CarritoCreate) -> Optional[models.Carrito]:
        return crud.actualizar_carrito(self.session, carrito_id, carrito)

    def delete(self, carrito_id: int) -> Optional[models.Carrito]:
        return crud.eliminar_carrito(self.session, carrito_id)
