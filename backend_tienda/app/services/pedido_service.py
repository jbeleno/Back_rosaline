"""Service layer for order-related business logic."""
from fastapi import HTTPException, status
from ..repositories.pedido_repository import PedidoRepository
from ..repositories.cliente_repository import ClienteRepository
from .. import schemas
from typing import List, Optional
from ..models import Pedido

class PedidoService:
    def __init__(self, pedido_repository: PedidoRepository, cliente_repository: ClienteRepository):
        self.pedido_repository = pedido_repository
        self.cliente_repository = cliente_repository

    def crear_pedido(self, pedido: schemas.PedidoCreate, current_user: dict):
        user_id = current_user.get("id_usuario")
        user_role = current_user.get("rol")

        if user_role not in ["admin", "super_admin"]:
            cliente = self.cliente_repository.get(pedido.id_cliente)
            if not cliente or cliente.id_usuario != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo puedes crear pedidos para tu propia cuenta"
                )
        return self.pedido_repository.create(pedido)

    def listar_pedidos(self, skip: int, limit: int, current_user: dict) -> List[Pedido]:
        es_admin = current_user.get("rol") in ["admin", "super_admin"]
        if es_admin:
            return self.pedido_repository.list(skip=skip, limit=limit)
        else:
            cliente = self.cliente_repository.get_by_usuario_id(current_user.get("id_usuario"))
            if not cliente:
                return []
            return self.pedido_repository.get_by_cliente_id(cliente.id_cliente, skip, limit)

    def listar_pedidos_por_cliente(self, cliente_id: int, current_user: dict, skip: int, limit: int) -> List[Pedido]:
        # First, check if the client exists to provide a 404 if not.
        cliente = self.cliente_repository.get_by_id(cliente_id)
        if not cliente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
        
        # Security Check
        es_admin = current_user.get("rol") in ["admin", "super_admin"]
        if not es_admin:
            # Check if the authenticated user is the owner of the client profile
            auth_user_cliente = self.cliente_repository.get_by_usuario_id(current_user.get("id_usuario"))
            if not auth_user_cliente or auth_user_cliente.id_cliente != cliente_id:
                 raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para ver los pedidos de este cliente")

        return self.pedido_repository.get_by_cliente_id(cliente_id, skip, limit)
        
    def listar_pedidos_por_estado(self, estado: str, current_user: dict, skip: int, limit: int) -> List[Pedido]:
        es_admin = current_user.get("rol") in ["admin", "super_admin"]
        if es_admin:
            return self.pedido_repository.get_by_estado(estado, skip, limit)
        else:
            cliente = self.cliente_repository.get_by_usuario_id(current_user.get("id_usuario"))
            if not cliente:
                return []
            return self.pedido_repository.get_by_estado_and_cliente_ids(estado, [cliente.id_cliente], skip, limit)

    def obtener_pedido(self, pedido_id: int, current_user: dict):
        pedido = self.pedido_repository.get(pedido_id)
        if not pedido:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
        
        user_id = current_user.get("id_usuario")
        user_role = current_user.get("rol")
        
        if user_role not in ["admin", "super_admin"]:
            cliente = self.cliente_repository.get(pedido.id_cliente)
            if not cliente or cliente.id_usuario != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo puedes ver tus propios pedidos")

        return pedido
    
    def actualizar_pedido(
        self, pedido_id: int, pedido_update: schemas.PedidoUpdate, current_user: dict
    ) -> Optional[Pedido]:
        self.obtener_pedido(pedido_id, current_user) # Reutiliza la lógica de validación de permisos
        return self.pedido_repository.update(pedido_id, pedido_update)

    def eliminar_pedido(self, pedido_id: int):
        db_pedido = self.pedido_repository.delete(pedido_id)
        if not db_pedido:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
        return db_pedido
