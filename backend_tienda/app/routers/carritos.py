from fastapi import APIRouter, Depends, status
from typing import List
from .. import schemas
from ..services.carrito_service import CarritoService
from ..core.dependencies import get_carrito_repository, get_cliente_repository, get_detalle_carrito_service
from ..auth import get_current_user, require_admin, require_cliente_or_admin
from ..services.detalle_carrito_service import DetalleCarritoService

router = APIRouter(
    prefix="/carritos",
    tags=["Carritos"]
)

def get_carrito_service(
    repo=Depends(get_carrito_repository),
    cliente_repo=Depends(get_cliente_repository)
) -> CarritoService:
    return CarritoService(repo, cliente_repo)

@router.post("/", summary="Crear carrito", status_code=status.HTTP_201_CREATED, response_model=schemas.Carrito)
def crear_carrito(
    carrito: schemas.CarritoCreate,
    current_user: dict = Depends(require_cliente_or_admin()),
    service: CarritoService = Depends(get_carrito_service)
):
    return service.crear_carrito(carrito, current_user)

@router.get("/", summary="Listar carritos", response_model=List[schemas.Carrito])
def listar_carritos(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(require_admin()),
    service: CarritoService = Depends(get_carrito_service)
):
    return service.listar_carritos(skip, limit)

@router.get("/{carrito_id}", summary="Obtener carrito por ID", response_model=schemas.Carrito)
def get_carrito(
    carrito_id: int,
    current_user: dict = Depends(get_current_user),
    service: CarritoService = Depends(get_carrito_service)
):
    return service.get_carrito(carrito_id, current_user)

@router.get("/{carrito_id}/productos", response_model=List[schemas.Producto], summary="Obtener productos de un carrito")
def obtener_productos_de_carrito(
    carrito_id: int,
    current_user: dict = Depends(get_current_user),
    service: DetalleCarritoService = Depends(get_detalle_carrito_service)
):
    return service.listar_productos_por_carrito(carrito_id, current_user)

@router.put("/{carrito_id}", summary="Actualizar carrito", response_model=schemas.Carrito)
def actualizar_carrito(
    carrito_id: int,
    carrito: schemas.CarritoCreate,
    current_user: dict = Depends(get_current_user),
    service: CarritoService = Depends(get_carrito_service)
):
    return service.actualizar_carrito(carrito_id, carrito, current_user)

@router.delete("/{carrito_id}", summary="Eliminar carrito", response_model=schemas.Carrito)
def eliminar_carrito(
    carrito_id: int,
    current_user: dict = Depends(get_current_user),
    service: CarritoService = Depends(get_carrito_service)
):
    return service.eliminar_carrito(carrito_id, current_user)

@router.get("/{cliente_id}/carritos", summary="Obtener carritos de un cliente", response_model=List[schemas.Carrito])
def carritos_de_cliente(
    cliente_id: int,
    current_user: dict = Depends(get_current_user),
    service: CarritoService = Depends(get_carrito_service)
):
    return service.carritos_de_cliente(cliente_id, current_user)
