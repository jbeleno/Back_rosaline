"""Repository wrapper for Producto persistence operations."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from .. import crud, models, schemas
from .base import Repository


class ProductoRepository(Repository):
    def __init__(self, session: Session):
        super().__init__(session)

    def list(self, skip: int = 0, limit: int = 100):
        return crud.get_productos(self.session, skip=skip, limit=limit)

    def create(self, producto: schemas.ProductoCreate) -> models.Producto:
        return crud.crear_producto(self.session, producto)

    def get(self, producto_id: int) -> Optional[models.Producto]:
        return crud.get_producto(self.session, producto_id)

    def update(self, producto_id: int, producto: schemas.ProductoCreate) -> Optional[models.Producto]:
        return crud.actualizar_producto(self.session, producto_id, producto)

    def delete(self, producto_id: int) -> Optional[models.Producto]:
        return crud.eliminar_producto(self.session, producto_id)
