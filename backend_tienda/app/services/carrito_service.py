"""Service layer for cart-related business logic."""
from fastapi import HTTPException, status
from typing import Optional
from ..repositories.carrito_repository import CarritoRepository
from ..repositories.cliente_repository import ClienteRepository
from .. import schemas
from .cliente_service import ClienteService

class CarritoService:
    def __init__(self, carrito_repository: CarritoRepository, cliente_repository: ClienteRepository):
        self.carrito_repository = carrito_repository
        self.cliente_repository = cliente_repository

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

    def crear_carrito(self, carrito: schemas.CarritoCreate, current_user: dict):
        user_id = current_user.get("id_usuario")
        user_role = current_user.get("rol")

        if user_role not in ["admin", "super_admin"]:
            cliente = self.cliente_repository.get(carrito.id_cliente)
            if not cliente or cliente.id_usuario != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo puedes crear carritos para tu propia cuenta"
                )
        return self.carrito_repository.create(carrito)

    def listar_carritos(self, skip: int, limit: int):
        return self.carrito_repository.list(skip, limit)
    
    def actualizar_carrito(self, carrito_id: int, carrito_update: schemas.CarritoCreate, current_user: dict):
        self._validar_permiso_carrito(carrito_id, current_user)
        return self.carrito_repository.update(carrito_id, carrito_update)

    def eliminar_carrito(self, carrito_id: int, current_user: dict):
        self._validar_permiso_carrito(carrito_id, current_user)
        db_carrito = self.carrito_repository.delete(carrito_id)
        if not db_carrito:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrito no encontrado")
        return db_carrito

    def carritos_de_cliente(self, cliente_id: int, current_user: dict):
        # Reutiliza la lógica de obtener cliente para validar permisos
        cliente_service = ClienteService(self.cliente_repository)
        cliente_service.obtener_cliente(cliente_id, current_user)
        return self.carrito_repository.get_by_cliente_id(cliente_id)
