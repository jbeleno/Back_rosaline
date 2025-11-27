from .. import models
from ..schemas import AuditLogCreate
from .base import Repository
from sqlalchemy.orm import Session
from typing import List, Optional

class AuditLogRepository(Repository):
    def __init__(self, session: Session):
        super().__init__(session)

    def create(self, audit_log: AuditLogCreate) -> models.AuditLog:
        db_audit_log = models.AuditLog(**audit_log.dict())
        self.session.add(db_audit_log)
        self.session.commit()
        self.session.refresh(db_audit_log)
        return db_audit_log

    def list(self, skip: int = 0, limit: int = 100, **filters) -> List[models.AuditLog]:
        query = self.session.query(models.AuditLog)
        
        # Aplicar filtros dinámicos
        if filters.get("tabla_nombre"):
            query = query.filter(models.AuditLog.tabla_nombre == filters["tabla_nombre"])
        if filters.get("registro_id"):
            query = query.filter(models.AuditLog.registro_id == filters["registro_id"])
        if filters.get("accion"):
            query = query.filter(models.AuditLog.accion == filters["accion"])
        if filters.get("usuario_id"):
            query = query.filter(models.AuditLog.usuario_id == filters["usuario_id"])
        if filters.get("fecha_desde"):
            query = query.filter(models.AuditLog.timestamp >= filters["fecha_desde"])
        if filters.get("fecha_hasta"):
            query = query.filter(models.AuditLog.timestamp <= filters["fecha_hasta"])
            
        return query.offset(skip).limit(limit).all()
