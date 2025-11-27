"""Service layer for product-related business logic."""
from fastapi import HTTPException, status
from ..repositories.producto_repository import ProductoRepository
from .. import schemas
from typing import Optional, List
from ..models import Producto

class ProductoService:
    def __init__(self, producto_repository: ProductoRepository):
        self.producto_repository = producto_repository

    def crear_producto(self, producto: schemas.ProductoCreate):
        # Verificar si ya existe un producto con el mismo nombre
        producto_existente = self.producto_repository.get_by_nombre(producto.nombre)
        
        if producto_existente:
            # Si existe, sumar la cantidad al stock actual
            stock_actualizado = producto_existente.cantidad + producto.cantidad
            update_data = schemas.ProductoUpdate(cantidad=stock_actualizado)
            return self.producto_repository.update(producto_existente.id_producto, update_data)
        else:
            # Si no existe, crear un nuevo producto
            return self.producto_repository.create(producto)

    def listar_productos(self, skip: int, limit: int):
        return self.producto_repository.list(skip, limit)

    def obtener_producto(self, producto_id: int):
        producto = self.producto_repository.get(producto_id)
        if not producto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
        return producto

    def listar_productos_por_categoria(self, categoria_id: int, skip: int, limit: int) -> List[Producto]:
        # We don't need a 404 check here, if the category doesn't exist, it will just return an empty list of products.
        return self.producto_repository.get_by_categoria_id(categoria_id, skip, limit)

    def actualizar_producto(self, producto_id: int, producto_update: schemas.ProductoCreate):
        db_producto = self.producto_repository.update(producto_id, producto_update)
        if not db_producto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
        return db_producto

    def eliminar_producto(self, producto_id: int):
        db_producto = self.producto_repository.delete(producto_id)
        if not db_producto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
        return {"mensaje": "Producto eliminado correctamente"}
    
    def productos_de_categoria(self, categoria_id: int):
        return self.producto_repository.get_by_categoria(categoria_id)
