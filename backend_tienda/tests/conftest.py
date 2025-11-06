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
from app.main import app, get_db
from app import models

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
    """Crea un usuario de prueba."""
    from app.crud import crear_usuario
    from app.schemas import UsuarioCreate
    
    usuario = crear_usuario(
        db_session,
        UsuarioCreate(
            correo="test@example.com",
            contraseña="password123",
            rol="cliente"
        )
    )
    return usuario


@pytest.fixture
def usuario_admin_test(db_session):
    """Crea un usuario admin de prueba."""
    from app.crud import crear_usuario
    from app.schemas import UsuarioCreate
    
    usuario = crear_usuario(
        db_session,
        UsuarioCreate(
            correo="admin@example.com",
            contraseña="admin123",
            rol="admin"
        )
    )
    return usuario


@pytest.fixture
def cliente_test(db_session, usuario_test):
    """Crea un cliente de prueba."""
    from app.crud import crear_cliente
    from app.schemas import ClienteCreate
    
    cliente = crear_cliente(
        db_session,
        ClienteCreate(
            id_usuario=usuario_test.id_usuario,
            nombre="Juan",
            apellido="Pérez",
            telefono="123456789",
            direccion="Calle Test 123"
        )
    )
    return cliente


@pytest.fixture
def categoria_test(db_session):
    """Crea una categoría de prueba."""
    from app.crud import crear_categoria
    from app.schemas import CategoriaCreate
    
    categoria = crear_categoria(
        db_session,
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
    """Crea un producto de prueba."""
    from app.crud import crear_producto
    from app.schemas import ProductoCreate
    
    producto = crear_producto(
        db_session,
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

