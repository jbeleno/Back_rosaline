"""Repository wrapper for Categoria persistence operations."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from .. import crud, models, schemas
from .base import Repository


class CategoriaRepository(Repository):
    def __init__(self, session: Session):
        super().__init__(session)

    def list(self, skip: int = 0, limit: int = 100):
        return crud.get_categorias(self.session, skip=skip, limit=limit)

    def create(self, categoria: schemas.CategoriaCreate) -> models.Categoria:
        return crud.crear_categoria(self.session, categoria)

    def get(self, categoria_id: int) -> Optional[models.Categoria]:
        return crud.get_categoria(self.session, categoria_id)

    def update(self, categoria_id: int, categoria: schemas.CategoriaCreate) -> Optional[models.Categoria]:
        return crud.actualizar_categoria(self.session, categoria_id, categoria)

    def delete(self, categoria_id: int) -> Optional[models.Categoria]:
        return crud.eliminar_categoria(self.session, categoria_id)
