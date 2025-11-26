"""Service layer for order detail-related business logic."""
from fastapi import HTTPException, status
from typing import Optional, List
from ..repositories.detalle_pedido_repository import DetallePedidoRepository
from ..repositories.pedido_repository import PedidoRepository
from ..repositories.cliente_repository import ClienteRepository
from .. import schemas
from .. import models

class DetallePedidoService:
    def __init__(self, detalle_pedido_repository: DetallePedidoRepository, pedido_repository: PedidoRepository, cliente_repository: ClienteRepository):
        self.detalle_pedido_repository = detalle_pedido_repository
        self.pedido_repository = pedido_repository
        self.cliente_repository = cliente_repository

    def _validar_permiso_pedido(self, pedido_id: int, current_user: dict):
        user_id = current_user.get("id_usuario")
        user_role = current_user.get("rol")

        if user_role not in ["admin", "super_admin"]:
            pedido = self.pedido_repository.get(pedido_id)
            if not pedido:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
            
            cliente = self.cliente_repository.get(pedido.id_cliente)
            if not cliente or cliente.id_usuario != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos sobre este pedido"
                )

    def crear_detalle_pedido(self, detalle: schemas.DetallePedidoCreate, current_user: dict):
        self._validar_permiso_pedido(detalle.id_pedido, current_user)
        return self.detalle_pedido_repository.create(detalle)

    def listar_detalles_pedido(self, skip: int, limit: int, pedido_id: Optional[int], current_user: dict):
        user_id = current_user.get("id_usuario")
        user_role = current_user.get("rol")

        if user_role in ["admin", "super_admin"]:
            return self.detalle_pedido_repository.list(skip=skip, limit=limit, pedido_id=pedido_id)
        
        # Lógica para clientes
        cliente = self.cliente_repository.get_by_usuario_id(user_id)
        if not cliente:
            return []
        
        pedidos_cliente_ids = [p.id_pedido for p in self.pedido_repository.get_by_cliente_id(cliente.id_cliente)]
        if not pedidos_cliente_ids:
            return []

        if pedido_id:
            if pedido_id not in pedidos_cliente_ids:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos sobre este pedido")
            return self.detalle_pedido_repository.list(skip=skip, limit=limit, pedido_id=pedido_id)
        
        return self.detalle_pedido_repository.list_by_pedido_ids(pedidos_cliente_ids, skip, limit)

    def actualizar_detalle_pedido(self, detalle_id: int, detalle_update: schemas.DetallePedidoCreate, current_user: dict):
        db_detalle = self.detalle_pedido_repository.get(detalle_id)
        if not db_detalle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detalle de pedido no encontrado")
        
        self._validar_permiso_pedido(db_detalle.id_pedido, current_user)
        return self.detalle_pedido_repository.update(detalle_id, detalle_update)

    def eliminar_detalle_pedido(self, detalle_id: int, current_user: dict):
        db_detalle = self.detalle_pedido_repository.get(detalle_id)
        if not db_detalle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detalle de pedido no encontrado")
        
        self._validar_permiso_pedido(db_detalle.id_pedido, current_user)
        return self.detalle_pedido_repository.delete(detalle_id)

    def listar_productos_por_pedido(self, pedido_id: int, current_user: dict) -> List[models.Producto]:
        # Security check is implicitly handled by get_pedido
        self.get_pedido(pedido_id, current_user) 
        return self.detalle_pedido_repository.get_productos_by_pedido_id(pedido_id)

    def productos_de_pedido(self, pedido_id: int, current_user: dict):
        self._validar_permiso_pedido(pedido_id, current_user)
        detalles = self.detalle_pedido_repository.list(pedido_id=pedido_id)
        return [d.producto for d in detalles if d.producto]
