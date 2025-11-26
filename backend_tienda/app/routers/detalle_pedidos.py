from fastapi import APIRouter, Depends, status
from typing import List, Optional
from .. import schemas
from ..services.detalle_pedido_service import DetallePedidoService
from ..core.dependencies import get_detalle_pedido_repository, get_pedido_repository, get_cliente_repository
from ..auth import get_current_user, require_cliente_or_admin

router = APIRouter(
    prefix="/detalle_pedidos",
    tags=["Pedidos"]
)

def get_detalle_pedido_service(
    repo=Depends(get_detalle_pedido_repository),
    pedido_repo=Depends(get_pedido_repository),
    cliente_repo=Depends(get_cliente_repository)
) -> DetallePedidoService:
    return DetallePedidoService(repo, pedido_repo, cliente_repo)

@router.post("/", summary="Crear detalle de pedido", status_code=status.HTTP_201_CREATED, response_model=schemas.DetallePedido)
def crear_detalle_pedido(
    detalle: schemas.DetallePedidoCreate,
    current_user: dict = Depends(require_cliente_or_admin),
    service: DetallePedidoService = Depends(get_detalle_pedido_service)
):
    return service.crear_detalle_pedido(detalle, current_user)

@router.get("/", summary="Listar detalles de pedidos", response_model=List[schemas.DetallePedido])
def listar_detalles_pedido(
    skip: int = 0,
    limit: int = 100,
    pedido_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    service: DetallePedidoService = Depends(get_detalle_pedido_service)
):
    return service.listar_detalles_pedido(skip, limit, pedido_id, current_user)

@router.put("/{detalle_id}", summary="Actualizar detalle de pedido", response_model=schemas.DetallePedido)
def actualizar_detalle_pedido(
    detalle_id: int,
    detalle: schemas.DetallePedidoCreate,
    current_user: dict = Depends(get_current_user),
    service: DetallePedidoService = Depends(get_detalle_pedido_service)
):
    return service.actualizar_detalle_pedido(detalle_id, detalle, current_user)

@router.delete("/{detalle_id}", summary="Eliminar detalle de pedido", response_model=schemas.DetallePedido)
def eliminar_detalle_pedido(
    detalle_id: int,
    current_user: dict = Depends(get_current_user),
    service: DetallePedidoService = Depends(get_detalle_pedido_service)
):
    return service.eliminar_detalle_pedido(detalle_id, current_user)

@router.get("/{pedido_id}/productos", summary="Obtener productos de un pedido", response_model=List[schemas.Producto])
def productos_de_pedido(
    pedido_id: int,
    current_user: dict = Depends(get_current_user),
    service: DetallePedidoService = Depends(get_detalle_pedido_service)
):
    return service.productos_de_pedido(pedido_id, current_user)
