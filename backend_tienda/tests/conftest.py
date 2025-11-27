import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Configurar variable de entorno para pruebas antes de importar la app
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_only_not_for_production"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://test.local"

from app.database import Base
from app.main import app
from app.core.dependencies import get_db
from app import models

# Importaciones de la nueva arquitectura
from app.repositories.usuario_repository import UsuarioRepository
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.producto_repository import ProductoRepository
from app.services.usuario_service import UsuarioService
from app.services.cliente_service import ClienteService
from app.services.categoria_service import CategoriaService
from app.services.producto_service import ProductoService
from unittest.mock import MagicMock

# Crear engine de prueba con SQLite en memoria
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Crea una sesión de base de datos para cada prueba."""
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    
    # Crear una sesión
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Limpiar tablas después de cada prueba
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Crea un cliente de prueba de FastAPI."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def usuario_test(db_session):
    """Crea un usuario de prueba usando la capa de servicio."""
    from app.schemas import UsuarioCreate

    # Mock del servicio de email para evitar envíos reales
    mock_email_service = MagicMock()

    usuario_repo = UsuarioRepository(db_session)
    usuario_service = UsuarioService(usuario_repo)
    
    # Sobrescribir el email_service a nivel de módulo para que el servicio lo use
    from app.services import usuario_service as usuario_service_module
    original_email_service = usuario_service_module.email_service
    usuario_service_module.email_service = mock_email_service

    usuario = usuario_service.crear_usuario(
        UsuarioCreate(
            correo="test@example.com",
            contraseña="password123",
            rol="cliente"
        )
    )
    
    # Restaurar el servicio de email original
    usuario_service_module.email_service = original_email_service
    
    # Confirmar usuario para que pueda loguearse en las pruebas
    usuario.email_verificado = "S"
    db_session.commit()
    db_session.refresh(usuario)
    
    return usuario


@pytest.fixture
def usuario_admin_test(db_session):
    """Crea un usuario admin de prueba usando la capa de servicio."""
    from app.schemas import UsuarioCreate

    mock_email_service = MagicMock()
    usuario_repo = UsuarioRepository(db_session)
    usuario_service = UsuarioService(usuario_repo)

    from app.services import usuario_service as usuario_service_module
    original_email_service = usuario_service_module.email_service
    usuario_service_module.email_service = mock_email_service

    usuario = usuario_service.crear_usuario(
        UsuarioCreate(
            correo="admin@example.com",
            contraseña="admin123",
            rol="admin"
        )
    )

    usuario_service_module.email_service = original_email_service
    
    usuario.email_verificado = "S"
    db_session.commit()
    db_session.refresh(usuario)
    
    return usuario


@pytest.fixture
def cliente_test(db_session, usuario_test):
    """Crea un cliente de prueba usando la capa de servicio."""
    from app.schemas import ClienteCreate

    cliente_repo = ClienteRepository(db_session)
    cliente_service = ClienteService(cliente_repo)
    
    # Para crear un cliente, el servicio espera un `current_user` (token decodificado)
    current_user_mock = {
        "id_usuario": usuario_test.id_usuario,
        "rol": usuario_test.rol
    }

    cliente = cliente_service.crear_cliente(
        ClienteCreate(
            id_usuario=usuario_test.id_usuario,
            nombre="Juan",
            apellido="Pérez",
            telefono="123456789",
            direccion="Calle Test 123"
        ),
        current_user=current_user_mock
    )
    return cliente


@pytest.fixture
def categoria_test(db_session):
    """Crea una categoría de prueba usando la capa de servicio."""
    from app.schemas import CategoriaCreate

    categoria_repo = CategoriaRepository(db_session)
    categoria_service = CategoriaService(categoria_repo)

    categoria = categoria_service.crear_categoria(
        CategoriaCreate(
            nombre="Electrónica",
            descripcion_corta="Dispositivos electrónicos",
            descripcion_larga="Todos los dispositivos electrónicos",
            estado="activo"
        )
    )
    return categoria


@pytest.fixture
def producto_test(db_session, categoria_test):
    """Crea un producto de prueba usando la capa de servicio."""
    from app.schemas import ProductoCreate

    producto_repo = ProductoRepository(db_session)
    producto_service = ProductoService(producto_repo)

    producto = producto_service.crear_producto(
        ProductoCreate(
            id_categoria=categoria_test.id_categoria,
            nombre="iPhone 15",
            descripcion="Smartphone de última generación",
            cantidad=50,
            precio=999.99,
            estado="activo"
        )
    )
    return producto


@pytest.fixture
def token_test(client, usuario_test):
    """Obtiene un token de autenticación de prueba."""
    response = client.post(
        "/login",
        json={
            "correo": usuario_test.correo,
            "contraseña": "password123"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def token_admin_test(client, usuario_admin_test):
    """Obtiene un token de admin de prueba."""
    response = client.post(
        "/login",
        json={
            "correo": usuario_admin_test.correo,
            "contraseña": "admin123"
        }
    )
    return response.json()["access_token"]


def get_auth_headers(token: str):
    """Helper para obtener headers de autenticación."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def usuario_sin_perfil_test(db_session):
    """Crea un usuario de prueba sin un perfil de cliente asociado."""
    from app.schemas import UsuarioCreate
    mock_email_service = MagicMock()
    usuario_repo = UsuarioRepository(db_session)
    usuario_service = UsuarioService(usuario_repo)
    
    from app.services import usuario_service as usuario_service_module
    original_email_service = usuario_service_module.email_service
    usuario_service_module.email_service = mock_email_service

    usuario = usuario_service.crear_usuario(
        UsuarioCreate(
            correo="user.sin.perfil@example.com",
            contraseña="password123",
            rol="cliente"
        )
    )
    
    usuario_service_module.email_service = original_email_service
    
    usuario.email_verificado = "S"
    db_session.commit()
    db_session.refresh(usuario)
    
    return usuario


@pytest.fixture
def token_sin_perfil_test(client, usuario_sin_perfil_test):
    """Obtiene un token para el usuario sin perfil de cliente."""
    response = client.post(
        "/login",
        json={
            "correo": usuario_sin_perfil_test.correo,
            "contraseña": "password123"
        }
    )
    return response.json()["access_token"]
