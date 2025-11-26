from fastapi import APIRouter, Depends, status
from typing import List
from .. import schemas
from ..services.producto_service import ProductoService
from ..core.dependencies import get_producto_repository
from ..auth import require_admin

router = APIRouter(
    prefix="/productos",
    tags=["Productos"]
)

def get_producto_service(repo=Depends(get_producto_repository)) -> ProductoService:
    return ProductoService(repo)

@router.post("/", summary="Crear producto", status_code=status.HTTP_201_CREATED, response_model=schemas.Producto)
def crear_producto(
    producto: schemas.ProductoCreate,
    current_user: dict = Depends(require_admin),
    service: ProductoService = Depends(get_producto_service)
):
    return service.crear_producto(producto)

@router.get("/", summary="Listar productos", response_model=List[schemas.Producto])
def listar_productos(
    skip: int = 0,
    limit: int = 100,
    service: ProductoService = Depends(get_producto_service)
):
    return service.listar_productos(skip, limit)

@router.get("/{producto_id}", summary="Obtener producto por ID", response_model=schemas.Producto)
def obtener_producto(
    producto_id: int,
    service: ProductoService = Depends(get_producto_service)
):
    return service.obtener_producto(producto_id)

@router.put("/{producto_id}", summary="Actualizar producto", response_model=schemas.Producto)
def actualizar_producto(
    producto_id: int,
    producto: schemas.ProductoCreate,
    current_user: dict = Depends(require_admin),
    service: ProductoService = Depends(get_producto_service)
):
    return service.actualizar_producto(producto_id, producto)

@router.delete("/{id}", summary="Eliminar producto")
def eliminar_producto(
    id: int,
    current_user: dict = Depends(require_admin),
    service: ProductoService = Depends(get_producto_service)
):
    return service.eliminar_producto(id)

@router.get("/categoria/{categoria_id}/productos", summary="Obtener productos por categoría", response_model=List[schemas.Producto])
def productos_de_categoria(
    categoria_id: int,
    service: ProductoService = Depends(get_producto_service)
):
    return service.productos_de_categoria(categoria_id)
