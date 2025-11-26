from fastapi import APIRouter, Depends, status
from typing import List
from .. import schemas
from ..services.pedido_service import PedidoService
from ..core.dependencies import get_pedido_repository, get_cliente_repository
from ..auth import get_current_user, require_admin, require_cliente_or_admin

router = APIRouter(
    prefix="/pedidos",
    tags=["Pedidos"]
)

def get_pedido_service(
    repo=Depends(get_pedido_repository),
    cliente_repo=Depends(get_cliente_repository)
) -> PedidoService:
    return PedidoService(repo, cliente_repo)

@router.post("/", summary="Crear pedido", status_code=status.HTTP_201_CREATED, response_model=schemas.Pedido)
def crear_pedido(
    pedido: schemas.PedidoCreate,
    current_user: dict = Depends(require_cliente_or_admin),
    service: PedidoService = Depends(get_pedido_service)
):
    return service.crear_pedido(pedido, current_user)

@router.get("/", summary="Listar pedidos", response_model=List[schemas.Pedido])
def listar_pedidos(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    service: PedidoService = Depends(get_pedido_service)
):
    return service.listar_pedidos(skip, limit, current_user)

@router.get("/{pedido_id}", summary="Obtener pedido por ID", response_model=schemas.Pedido)
def obtener_pedido(
    pedido_id: int,
    current_user: dict = Depends(get_current_user),
    service: PedidoService = Depends(get_pedido_service)
):
    return service.obtener_pedido(pedido_id, current_user)

@router.put("/{pedido_id}", summary="Actualizar pedido", response_model=schemas.Pedido)
def actualizar_pedido(
    pedido_id: int,
    pedido: schemas.PedidoCreate,
    current_user: dict = Depends(get_current_user),
    service: PedidoService = Depends(get_pedido_service)
):
    return service.actualizar_pedido(pedido_id, pedido, current_user)

@router.delete("/{pedido_id}", summary="Eliminar pedido", response_model=schemas.Pedido)
def eliminar_pedido(
    pedido_id: int,
    current_user: dict = Depends(require_admin),
    service: PedidoService = Depends(get_pedido_service)
):
    return service.eliminar_pedido(pedido_id)

@router.get("/estado/{estado}", summary="Listar pedidos por estado", response_model=List[schemas.Pedido])
def listar_pedidos_por_estado(
    estado: str,
    current_user: dict = Depends(get_current_user),
    service: PedidoService = Depends(get_pedido_service)
):
    return service.listar_pedidos_por_estado(estado, current_user)
