from fastapi import APIRouter, Depends, status
from typing import List
from .. import schemas
from ..services.cliente_service import ClienteService
from ..core.dependencies import get_cliente_repository
from ..auth import get_current_user, require_admin, require_cliente_or_admin

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)

def get_cliente_service(repo=Depends(get_cliente_repository)) -> ClienteService:
    return ClienteService(repo)

@router.post("/", summary="Crear cliente", status_code=status.HTTP_201_CREATED, response_model=schemas.Cliente)
def crear_cliente(
    cliente: schemas.ClienteCreate,
    current_user: dict = Depends(require_cliente_or_admin),
    service: ClienteService = Depends(get_cliente_service)
):
    return service.crear_cliente(cliente, current_user)

@router.get("/", summary="Listar clientes", response_model=List[schemas.Cliente])
def listar_clientes(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(require_admin),
    service: ClienteService = Depends(get_cliente_service)
):
    return service.listar_clientes(skip, limit)

@router.get("/usuario/{id_usuario}", summary="Obtener cliente por ID de usuario", response_model=schemas.Cliente)
def obtener_cliente_por_usuario(
    id_usuario: int,
    current_user: dict = Depends(get_current_user),
    service: ClienteService = Depends(get_cliente_service)
):
    return service.obtener_cliente_por_usuario(id_usuario, current_user)

@router.get("/{cliente_id}", summary="Obtener cliente por ID", response_model=schemas.Cliente)
def obtener_cliente(
    cliente_id: int,
    current_user: dict = Depends(get_current_user),
    service: ClienteService = Depends(get_cliente_service)
):
    return service.obtener_cliente(cliente_id, current_user)

@router.put("/{cliente_id}", summary="Actualizar cliente", response_model=schemas.Cliente)
def actualizar_cliente(
    cliente_id: int,
    cliente: schemas.ClienteCreate,
    current_user: dict = Depends(get_current_user),
    service: ClienteService = Depends(get_cliente_service)
):
    return service.actualizar_cliente(cliente_id, cliente, current_user)

@router.delete("/{cliente_id}", summary="Eliminar cliente", response_model=schemas.Cliente)
def eliminar_cliente(
    cliente_id: int,
    current_user: dict = Depends(require_admin),
    service: ClienteService = Depends(get_cliente_service)
):
    return service.eliminar_cliente(cliente_id)
