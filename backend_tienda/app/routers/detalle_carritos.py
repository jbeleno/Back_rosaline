from fastapi import APIRouter, Depends, status
from typing import List, Optional
from .. import schemas
from ..services.detalle_carrito_service import DetalleCarritoService
from ..core.dependencies import get_detalle_carrito_repository, get_carrito_repository, get_cliente_repository
from ..auth import get_current_user, require_cliente_or_admin

router = APIRouter(
    prefix="/detalle_carrito",
    tags=["Carritos"]
)

def get_detalle_carrito_service(
    repo=Depends(get_detalle_carrito_repository),
    carrito_repo=Depends(get_carrito_repository),
    cliente_repo=Depends(get_cliente_repository)
) -> DetalleCarritoService:
    return DetalleCarritoService(repo, carrito_repo, cliente_repo)

@router.post("/", summary="Crear detalle de carrito", status_code=status.HTTP_201_CREATED, response_model=schemas.DetalleCarrito)
def crear_detalle_carrito(
    detalle: schemas.DetalleCarritoCreate,
    current_user: dict = Depends(require_cliente_or_admin),
    service: DetalleCarritoService = Depends(get_detalle_carrito_service)
):
    return service.crear_detalle_carrito(detalle, current_user)

@router.get("/", summary="Listar detalles de carrito", response_model=List[schemas.DetalleCarrito])
def listar_detalles_carrito(
    skip: int = 0,
    limit: int = 100,
    carrito_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    service: DetalleCarritoService = Depends(get_detalle_carrito_service)
):
    return service.listar_detalles_carrito(skip, limit, carrito_id, current_user)

@router.put("/{detalle_id}", summary="Actualizar detalle de carrito", response_model=schemas.DetalleCarrito)
def actualizar_detalle_carrito(
    detalle_id: int,
    detalle: schemas.DetalleCarritoCreate,
    current_user: dict = Depends(get_current_user),
    service: DetalleCarritoService = Depends(get_detalle_carrito_service)
):
    return service.actualizar_detalle_carrito(detalle_id, detalle, current_user)

@router.delete("/{detalle_id}", summary="Eliminar detalle de carrito")
def eliminar_detalle_carrito(
    detalle_id: int,
    current_user: dict = Depends(get_current_user),
    service: DetalleCarritoService = Depends(get_detalle_carrito_service)
):
    return service.eliminar_detalle_carrito(detalle_id, current_user)

@router.get("/{carrito_id}/productos", summary="Obtener productos de un carrito", response_model=List[schemas.Producto])
def productos_de_carrito(
    carrito_id: int,
    current_user: dict = Depends(get_current_user),
    service: DetalleCarritoService = Depends(get_detalle_carrito_service)
):
    return service.productos_de_carrito(carrito_id, current_user)
