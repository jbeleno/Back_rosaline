"""Service layer for client-related business logic."""
from fastapi import HTTPException, status
from ..repositories.cliente_repository import ClienteRepository
from .. import schemas
from typing import Optional
from ..models import Cliente

class ClienteService:
    def __init__(self, cliente_repository: ClienteRepository):
        self.cliente_repository = cliente_repository

    def crear_cliente(self, cliente: schemas.ClienteCreate, current_user: dict):
        user_id = current_user.get("id_usuario")
        user_role = current_user.get("rol")
        
        if user_role not in ["admin", "super_admin"] and cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo puedes crear tu propio perfil de cliente"
            )
        
        return self.cliente_repository.create(cliente)

    def listar_clientes(self, skip: int, limit: int):
        return self.cliente_repository.list(skip, limit)

    def obtener_cliente_por_usuario(self, id_usuario: int, current_user: dict):
        user_id_from_token = current_user.get("id_usuario")
        user_role = current_user.get("rol")
        if user_role not in ["admin", "super_admin"] and id_usuario != user_id_from_token:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para ver este perfil")

        cliente = self.cliente_repository.get_by_usuario_id(id_usuario)
        if not cliente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
        return cliente

    def obtener_cliente(self, cliente_id: int, current_user: dict):
        cliente = self.cliente_repository.get(cliente_id)
        if not cliente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
        
        user_id_from_token = current_user.get("id_usuario")
        user_role = current_user.get("rol")
        
        if user_role not in ["admin", "super_admin"] and cliente.id_usuario != user_id_from_token:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo puedes ver tu propio perfil")
        
        return cliente

    def actualizar_cliente(self, cliente_id: int, cliente_update: schemas.ClienteCreate, current_user: dict):
        db_cliente = self.obtener_cliente(cliente_id, current_user) # Reutiliza la validación de permisos
        return self.cliente_repository.update(db_cliente.id_cliente, cliente_update)

    def eliminar_cliente(self, cliente_id: int):
        db_cliente = self.cliente_repository.delete(cliente_id)
        if not db_cliente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
        return db_cliente

    def get_cliente_by_usuario_id(self, usuario_id: int) -> Optional[Cliente]:
        db_cliente = self.cliente_repository.get_by_usuario_id(usuario_id)
        if not db_cliente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de cliente no encontrado para este usuario")
        return db_cliente
