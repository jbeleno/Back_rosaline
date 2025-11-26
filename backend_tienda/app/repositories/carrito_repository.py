"""Repository wrapper for Carrito persistence operations."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from .. import crud, models, schemas
from .base import Repository


class CarritoRepository(Repository):
    def __init__(self, session: Session):
        super().__init__(session)

    def list(self, skip: int = 0, limit: int = 100):
        return crud.get_carritos(self.session, skip=skip, limit=limit)

    def create(self, carrito: schemas.CarritoCreate) -> models.Carrito:
        return crud.crear_carrito(self.session, carrito)

    def get(self, carrito_id: int) -> Optional[models.Carrito]:
        return crud.get_carrito(self.session, carrito_id)

    def update(self, carrito_id: int, carrito: schemas.CarritoCreate) -> Optional[models.Carrito]:
        return crud.actualizar_carrito(self.session, carrito_id, carrito)

    def delete(self, carrito_id: int) -> Optional[models.Carrito]:
        return crud.eliminar_carrito(self.session, carrito_id)
