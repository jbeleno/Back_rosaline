"""Service layer for cart detail-related business logic."""
from fastapi import HTTPException, status
from typing import Optional
from ..repositories.detalle_carrito_repository import DetalleCarritoRepository
from ..repositories.carrito_repository import CarritoRepository
from ..repositories.cliente_repository import ClienteRepository
from ..repositories.producto_repository import ProductoRepository # Importar
from .. import schemas

class DetalleCarritoService:
    def __init__(
        self, 
        detalle_carrito_repository: DetalleCarritoRepository, 
        carrito_repository: CarritoRepository, 
        cliente_repository: ClienteRepository,
        producto_repository: ProductoRepository  # Añadir
    ):
        self.detalle_carrito_repository = detalle_carrito_repository
        self.carrito_repository = carrito_repository
        self.cliente_repository = cliente_repository
        self.producto_repository = producto_repository # Añadir

    def _validar_permiso_carrito(self, carrito_id: int, current_user: dict):
        user_id = current_user.get("id_usuario")
        user_role = current_user.get("rol")

        if user_role not in ["admin", "super_admin"]:
            carrito = self.carrito_repository.get(carrito_id)
            if not carrito:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrito no encontrado")
            
            cliente = self.cliente_repository.get(carrito.id_cliente)
            if not cliente or cliente.id_usuario != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos sobre este carrito"
                )

    def crear_detalle_carrito(self, detalle: schemas.DetalleCarritoCreate, current_user: dict):
        self._validar_permiso_carrito(detalle.id_carrito, current_user)

        # 1. Validar stock del producto
        producto = self.producto_repository.get(detalle.id_producto)
        if not producto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
        if producto.cantidad < detalle.cantidad:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay suficiente inventario para este producto")

        # 2. Buscar si el producto ya está en el carrito
        item_existente = self.detalle_carrito_repository.get_by_carrito_and_producto(
            carrito_id=detalle.id_carrito, 
            producto_id=detalle.id_producto
        )

        if item_existente:
            # 3. Si existe, actualizar la cantidad
            nueva_cantidad = item_existente.cantidad + detalle.cantidad
            if producto.cantidad < nueva_cantidad:
                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La cantidad total supera el inventario disponible")
            
            update_data = schemas.DetalleCarritoUpdate(cantidad=nueva_cantidad)
            return self.detalle_carrito_repository.update(item_existente.id_detalle_carrito, update_data)
        else:
            # 4. Si no existe, crear el nuevo detalle
            return self.detalle_carrito_repository.create(detalle)

    def listar_detalles_carrito(self, skip: int, limit: int, carrito_id: Optional[int], current_user: dict):
        user_id = current_user.get("id_usuario")
        user_role = current_user.get("rol")

        if user_role in ["admin", "super_admin"]:
            return self.detalle_carrito_repository.list(skip=skip, limit=limit, carrito_id=carrito_id)
        
        cliente = self.cliente_repository.get_by_usuario_id(user_id)
        if not cliente:
            return []
        
        carritos_cliente_ids = [c.id_carrito for c in self.carrito_repository.get_by_cliente_id(cliente.id_cliente)]
        if not carritos_cliente_ids:
            return []

        if carrito_id:
            if carrito_id not in carritos_cliente_ids:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos sobre este carrito")
            return self.detalle_carrito_repository.list(skip=skip, limit=limit, carrito_id=carrito_id)
        
        return self.detalle_carrito_repository.list_by_carrito_ids(carritos_cliente_ids, skip, limit)

    def actualizar_detalle_carrito(self, detalle_id: int, detalle_update: schemas.DetalleCarritoCreate, current_user: dict):
        db_detalle = self.detalle_carrito_repository.get(detalle_id)
        if not db_detalle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detalle de carrito no encontrado")
        
        self._validar_permiso_carrito(db_detalle.id_carrito, current_user)
        return self.detalle_carrito_repository.update(detalle_id, detalle_update)

    def eliminar_detalle_carrito(self, detalle_id: int, current_user: dict):
        db_detalle = self.detalle_carrito_repository.get(detalle_id)
        if not db_detalle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detalle de carrito no encontrado")
        
        self._validar_permiso_carrito(db_detalle.id_carrito, current_user)
        return self.detalle_carrito_repository.delete(detalle_id)

    def productos_de_carrito(self, carrito_id: int, current_user: dict):
        self._validar_permiso_carrito(carrito_id, current_user)
        detalles = self.detalle_carrito_repository.list(carrito_id=carrito_id)
        return [d.producto for d in detalles if d.producto]

    def listar_productos_por_carrito(self, carrito_id: int, current_user: dict):
        self._validar_permiso_carrito(carrito_id, current_user)
        # Security check is implicitly handled by get_carrito
        self.carrito_repository.get(carrito_id)
        return self.detalle_carrito_repository.get_productos_by_carrito_id(carrito_id)
