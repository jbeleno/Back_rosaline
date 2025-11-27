"""Repository wrapper for cart detail persistence operations."""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from .. import models, schemas
from .base import Repository

class DetalleCarritoRepository(Repository):
    def __init__(self, session: Session):
        super().__init__(session)

    def get(self, detalle_id: int) -> Optional[models.DetalleCarrito]:
        return self.session.query(models.DetalleCarrito).filter(models.DetalleCarrito.id_detalle_carrito == detalle_id).first()

    def get_by_carrito_and_producto(self, carrito_id: int, producto_id: int) -> Optional[models.DetalleCarrito]:
        return self.session.query(models.DetalleCarrito).filter(
            models.DetalleCarrito.id_carrito == carrito_id,
            models.DetalleCarrito.id_producto == producto_id
        ).first()

    def get_by_carrito_id(self, carrito_id: int, skip: int = 0, limit: int = 100) -> List[models.DetalleCarrito]:
        return self.session.query(models.DetalleCarrito).filter(models.DetalleCarrito.id_carrito == carrito_id).offset(skip).limit(limit).all()

    def get_productos_by_carrito_id(self, carrito_id: int) -> List[models.Producto]:
        return self.session.query(models.Producto).join(models.DetalleCarrito).filter(models.DetalleCarrito.id_carrito == carrito_id).all()

    def create(self, detalle: schemas.DetalleCarritoCreate) -> models.DetalleCarrito:
        db_detalle = models.DetalleCarrito(**detalle.model_dump())
        self.add(db_detalle)
        self.commit()
        self.refresh(db_detalle)
        return db_detalle

    def list(self, skip: int = 0, limit: int = 100, carrito_id: Optional[int] = None) -> List[models.DetalleCarrito]:
        query = self.session.query(models.DetalleCarrito)
        if carrito_id:
            query = query.filter(models.DetalleCarrito.id_carrito == carrito_id)
        return query.offset(skip).limit(limit).all()
    
    def list_by_carrito_ids(self, carrito_ids: List[int], skip: int = 0, limit: int = 100) -> List[models.DetalleCarrito]:
        return self.session.query(models.DetalleCarrito).filter(models.DetalleCarrito.id_carrito.in_(carrito_ids)).offset(skip).limit(limit).all()

    def update(self, detalle_id: int, detalle_update: schemas.DetalleCarritoCreate) -> Optional[models.DetalleCarrito]:
        db_detalle = self.get(detalle_id)
        if db_detalle:
            for key, value in detalle_update.model_dump().items():
                setattr(db_detalle, key, value)
            self.commit()
            self.refresh(db_detalle)
        return db_detalle

    def delete(self, detalle_id: int) -> Optional[models.DetalleCarrito]:
        db_detalle = self.get(detalle_id)
        if db_detalle:
            # Eager load relationships before expunging and deleting
            self.session.query(models.DetalleCarrito).options(
                joinedload(models.DetalleCarrito.carrito),
                joinedload(models.DetalleCarrito.producto)
            ).filter(models.DetalleCarrito.id_detalle_carrito == detalle_id).one()
            
            self.expunge(db_detalle)
            self.session.delete(db_detalle)
            self.commit()
        return db_detalle
