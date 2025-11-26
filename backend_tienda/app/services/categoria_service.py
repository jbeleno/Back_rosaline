"""Service layer for business logic."""
from fastapi import HTTPException, status
from ..repositories.categoria_repository import CategoriaRepository
from .. import schemas

class CategoriaService:
    def __init__(self, categoria_repository: CategoriaRepository):
        self.categoria_repository = categoria_repository

    def crear_categoria(self, categoria: schemas.CategoriaCreate):
        return self.categoria_repository.create(categoria)

    def listar_categorias(self, skip: int, limit: int):
        return self.categoria_repository.list(skip, limit)

    def obtener_categoria(self, categoria_id: int):
        categoria = self.categoria_repository.get(categoria_id)
        if not categoria:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
        return categoria

    def actualizar_categoria(self, categoria_id: int, categoria_update: schemas.CategoriaCreate):
        db_categoria = self.categoria_repository.update(categoria_id, categoria_update)
        if not db_categoria:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
        return db_categoria

    def eliminar_categoria(self, categoria_id: int):
        db_categoria = self.categoria_repository.delete(categoria_id)
        if not db_categoria:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
        return db_categoria
