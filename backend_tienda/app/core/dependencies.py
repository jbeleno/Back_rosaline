"""Common dependency providers for the FastAPI application."""

from __future__ import annotations

from functools import lru_cache
from typing import Generator, Type

from fastapi import Depends
from sqlalchemy.orm import Session

from ..auth import AuthService
from ..database import SessionLocal
from ..email_service import EmailService
from ..repositories.base import Repository
from ..repositories.usuario_repository import UsuarioRepository
from ..repositories.cliente_repository import ClienteRepository
from ..repositories.categoria_repository import CategoriaRepository
from ..repositories.producto_repository import ProductoRepository
from ..repositories.pedido_repository import PedidoRepository
from ..repositories.detalle_pedido_repository import DetallePedidoRepository
from ..repositories.carrito_repository import CarritoRepository
from ..repositories.detalle_carrito_repository import DetalleCarritoRepository
from ..repositories.audit_log_repository import AuditLogRepository

# Import Services
from ..services.usuario_service import UsuarioService
from ..services.cliente_service import ClienteService
from ..services.categoria_service import CategoriaService
from ..services.producto_service import ProductoService
from ..services.pedido_service import PedidoService
from ..services.detalle_pedido_service import DetallePedidoService
from ..services.carrito_service import CarritoService
from ..services.detalle_carrito_service import DetalleCarritoService
from ..services.audit_log_service import AuditLogService


# Dependencia para obtener la sesión de la base de datos
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@lru_cache()
def get_email_service() -> EmailService:
    return EmailService()


@lru_cache()
def get_auth_service() -> AuthService:
    return AuthService()


def get_repository(repo_type: Type[Repository]) -> Type[Repository]:
    def _get_repo(db: Session = Depends(get_db)) -> Repository:
        return repo_type(db)
    return _get_repo

# Repository Providers
def get_usuario_repository(db: Session = Depends(get_db)) -> UsuarioRepository:
    return UsuarioRepository(db)

def get_cliente_repository(db: Session = Depends(get_db)) -> ClienteRepository:
    return ClienteRepository(db)

def get_categoria_repository(db: Session = Depends(get_db)) -> CategoriaRepository:
    return CategoriaRepository(db)

def get_producto_repository(db: Session = Depends(get_db)) -> ProductoRepository:
    return ProductoRepository(db)

def get_pedido_repository(db: Session = Depends(get_db)) -> PedidoRepository:
    return PedidoRepository(db)

def get_detalle_pedido_repository(db: Session = Depends(get_db)) -> DetallePedidoRepository:
    return DetallePedidoRepository(db)

def get_carrito_repository(db: Session = Depends(get_db)) -> CarritoRepository:
    return CarritoRepository(db)

def get_detalle_carrito_repository(db: Session = Depends(get_db)) -> DetalleCarritoRepository:
    return DetalleCarritoRepository(db)

def get_audit_log_repository(db: Session = Depends(get_db)) -> AuditLogRepository:
    return AuditLogRepository(db)

# Service Providers
def get_usuario_service(repo: UsuarioRepository = Depends(get_usuario_repository)) -> UsuarioService:
    return UsuarioService(repo)

def get_cliente_service(
    repo: ClienteRepository = Depends(get_cliente_repository),
    usuario_repo: UsuarioRepository = Depends(get_usuario_repository)
) -> ClienteService:
    return ClienteService(repo, usuario_repo)

def get_categoria_service(repo: CategoriaRepository = Depends(get_categoria_repository)) -> CategoriaService:
    return CategoriaService(repo)

def get_producto_service(repo: ProductoRepository = Depends(get_producto_repository)) -> ProductoService:
    return ProductoService(repo)

def get_pedido_service(
    repo: PedidoRepository = Depends(get_pedido_repository),
    cliente_repo: ClienteRepository = Depends(get_cliente_repository)
) -> PedidoService:
    return PedidoService(repo, cliente_repo)

def get_detalle_pedido_service(
    repo: DetallePedidoRepository = Depends(get_detalle_pedido_repository),
    pedido_repo: PedidoRepository = Depends(get_pedido_repository),
    cliente_repo: ClienteRepository = Depends(get_cliente_repository)
) -> DetallePedidoService:
    return DetallePedidoService(repo, pedido_repo, cliente_repo)

def get_carrito_service(
    repo: CarritoRepository = Depends(get_carrito_repository),
    cliente_repo: ClienteRepository = Depends(get_cliente_repository)
) -> CarritoService:
    return CarritoService(repo, cliente_repo)

def get_detalle_carrito_service(
    repo: DetalleCarritoRepository = Depends(get_detalle_carrito_repository),
    carrito_repo: CarritoRepository = Depends(get_carrito_repository),
    cliente_repo: ClienteRepository = Depends(get_cliente_repository)
) -> DetalleCarritoService:
    return DetalleCarritoService(repo, carrito_repo, cliente_repo)

def get_audit_log_service(repo: AuditLogRepository = Depends(get_audit_log_repository)) -> AuditLogService:
    return AuditLogService(repo)
