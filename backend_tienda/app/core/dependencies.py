"""Common dependency providers for the FastAPI application."""

from __future__ import annotations

from functools import lru_cache
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from ..auth import AuthService
from ..database import SessionLocal
from ..email_service import EmailService
from ..repositories.carrito_repository import CarritoRepository
from ..repositories.categoria_repository import CategoriaRepository
from ..repositories.cliente_repository import ClienteRepository
from ..repositories.pedido_repository import PedidoRepository
from ..repositories.producto_repository import ProductoRepository
from ..repositories.usuario_repository import UsuarioRepository
from ..repositories.detalle_pedido_repository import DetallePedidoRepository
from ..repositories.detalle_carrito_repository import DetalleCarritoRepository
from ..services.carrito_service import CarritoService
from ..services.categoria_service import CategoriaService
from ..services.cliente_service import ClienteService
from ..services.pedido_service import PedidoService
from ..services.producto_service import ProductoService
from ..services.usuario_service import UsuarioService


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


# Dependencias para obtener los repositorios
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


def get_usuario_service(
    usuario_repository: UsuarioRepository = Depends(get_usuario_repository),
    cliente_repository: ClienteRepository = Depends(get_cliente_repository),
    email_service: EmailService = Depends(get_email_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> UsuarioService:
    return UsuarioService(usuario_repository, cliente_repository, email_service, auth_service)


def get_cliente_service(
    cliente_repository: ClienteRepository = Depends(get_cliente_repository),
) -> ClienteService:
    return ClienteService(cliente_repository)


def get_categoria_service(
    categoria_repository: CategoriaRepository = Depends(get_categoria_repository),
) -> CategoriaService:
    return CategoriaService(categoria_repository)


def get_producto_service(
    producto_repository: ProductoRepository = Depends(get_producto_repository),
    categoria_repository: CategoriaRepository = Depends(get_categoria_repository),
) -> ProductoService:
    return ProductoService(producto_repository, categoria_repository)


def get_pedido_service(
    pedido_repository: PedidoRepository = Depends(get_pedido_repository),
    producto_repository: ProductoRepository = Depends(get_producto_repository),
    cliente_repository: ClienteRepository = Depends(get_cliente_repository),
) -> PedidoService:
    return PedidoService(pedido_repository, producto_repository, cliente_repository)


def get_carrito_service(
    carrito_repository: CarritoRepository = Depends(get_carrito_repository),
    producto_repository: ProductoRepository = Depends(get_producto_repository),
    cliente_repository: ClienteRepository = Depends(get_cliente_repository),
) -> CarritoService:
    return CarritoService(carrito_repository, producto_repository, cliente_repository)
