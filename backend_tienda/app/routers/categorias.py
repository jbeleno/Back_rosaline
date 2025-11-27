from fastapi import APIRouter, Depends, status
from typing import List
from .. import schemas
from ..services.categoria_service import CategoriaService
from ..core.dependencies import get_categoria_repository, get_producto_service
from ..auth import require_admin
from ..services.producto_service import ProductoService

router = APIRouter(
    prefix="/categorias",
    tags=["Categorías"]
)

def get_categoria_service(repo=Depends(get_categoria_repository)) -> CategoriaService:
    return CategoriaService(repo)

@router.post("/", summary="Crear categoría", status_code=status.HTTP_201_CREATED, response_model=schemas.Categoria)
def crear_categoria(
    categoria: schemas.CategoriaCreate,
    current_user: dict = Depends(require_admin()),
    service: CategoriaService = Depends(get_categoria_service)
):
    return service.crear_categoria(categoria)

@router.get("/", summary="Listar categorías", response_model=List[schemas.Categoria])
def listar_categorias(
    skip: int = 0,
    limit: int = 100,
    service: CategoriaService = Depends(get_categoria_service)
):
    return service.listar_categorias(skip, limit)

@router.get("/{categoria_id}", summary="Obtener categoría por ID", response_model=schemas.Categoria)
def obtener_categoria(
    categoria_id: int,
    service: CategoriaService = Depends(get_categoria_service)
):
    return service.obtener_categoria(categoria_id)

@router.get("/{categoria_id}/productos", response_model=List[schemas.Producto], summary="Obtener productos de una categoría")
def obtener_productos_de_categoria(
    categoria_id: int,
    skip: int = 0,
    limit: int = 100,
    producto_service: ProductoService = Depends(get_producto_service)
):
    return producto_service.listar_productos_por_categoria(categoria_id, skip, limit)

@router.put("/{categoria_id}", summary="Actualizar categoría", response_model=schemas.Categoria)
def actualizar_categoria(
    categoria_id: int,
    categoria: schemas.CategoriaCreate,
    current_user: dict = Depends(require_admin()),
    service: CategoriaService = Depends(get_categoria_service)
):
    return service.actualizar_categoria(categoria_id, categoria)

@router.delete("/{categoria_id}", summary="Eliminar categoría", response_model=schemas.Categoria)
def eliminar_categoria(
    categoria_id: int,
    current_user: dict = Depends(require_admin()),
    service: CategoriaService = Depends(get_categoria_service)
):
    return service.eliminar_categoria(categoria_id)
