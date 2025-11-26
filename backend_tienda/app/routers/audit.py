from fastapi import APIRouter, Depends, Query, Path
from typing import List, Optional
from datetime import datetime
from .. import schemas, crud
from ..core.dependencies import get_db
from ..auth import require_admin
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/audit",
    tags=["Auditoría"]
)

@router.get("/", summary="Listar logs de auditoría", response_model=List[schemas.AuditLog])
def listar_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    tabla_nombre: Optional[str] = Query(None),
    registro_id: Optional[int] = Query(None),
    accion: Optional[str] = Query(None),
    usuario_id: Optional[int] = Query(None),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return crud.get_audit_logs(
        db, skip, limit, tabla_nombre, registro_id, accion, usuario_id, fecha_desde, fecha_hasta
    )

@router.get("/{tabla_nombre}/{registro_id}", summary="Obtener historial de un registro", response_model=List[schemas.AuditLog])
def obtener_historial_registro(
    tabla_nombre: str = Path(...),
    registro_id: int = Path(...),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return crud.get_audit_logs(db, tabla_nombre=tabla_nombre, registro_id=registro_id)
