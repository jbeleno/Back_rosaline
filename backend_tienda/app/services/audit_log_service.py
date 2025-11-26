from ..repositories.audit_log_repository import AuditLogRepository
from .. import models, schemas
from typing import List, Optional

class AuditLogService:
    def __init__(self, audit_log_repository: AuditLogRepository):
        self.audit_log_repository = audit_log_repository

    def listar_logs(self, skip: int, limit: int, filtros: dict) -> List[models.AuditLog]:
        return self.audit_log_repository.list_with_filters(skip=skip, limit=limit, **filtros)

    def obtener_historial_registro(self, tabla_nombre: str, registro_id: int, skip: int, limit: int) -> List[models.AuditLog]:
        return self.audit_log_repository.get_by_record(tabla_nombre, registro_id, skip, limit)
