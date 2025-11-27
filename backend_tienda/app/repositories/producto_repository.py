"""Repository wrapper for Producto persistence operations."""

from __future__ import annotations

from typing import Optional, List

from sqlalchemy.orm import Session, joinedload

from .. import crud, models, schemas
from .base import Repository


class ProductoRepository(Repository):
    def __init__(self, session: Session):
        super().__init__(session)

    def get_by_id(self, producto_id: int) -> Optional[models.Producto]:
        return self.session.query(models.Producto).options(joinedload(models.Producto.categoria)).filter(models.Producto.id_producto == producto_id).first()

    def get_by_nombre(self, nombre: str) -> Optional[models.Producto]:
        return self.session.query(models.Producto).filter(models.Producto.nombre == nombre).first()

    def get_by_categoria_id(self, categoria_id: int, skip: int = 0, limit: int = 100) -> List[models.Producto]:
        return self.session.query(models.Producto).filter(models.Producto.id_categoria == categoria_id).offset(skip).limit(limit).all()

    def list(self, skip: int = 0, limit: int = 100) -> List[models.Producto]:
        return self.session.query(models.Producto).options(joinedload(models.Producto.categoria)).offset(skip).limit(limit).all()

    def create(self, producto: schemas.ProductoCreate) -> models.Producto:
        return crud.crear_producto(self.session, producto)

    def get(self, producto_id: int) -> Optional[models.Producto]:
        return crud.get_producto(self.session, producto_id)

    def update(self, producto_id: int, producto: schemas.ProductoCreate) -> Optional[models.Producto]:
        return crud.actualizar_producto(self.session, producto_id, producto)

    def delete(self, producto_id: int) -> Optional[models.Producto]:
        return crud.eliminar_producto(self.session, producto_id)
