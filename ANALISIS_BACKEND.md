# Análisis del Backend - Rosaline Bakery

## 📋 Resumen Ejecutivo

El backend de Rosaline Bakery es una API REST desarrollada con **FastAPI** que está en proceso de refactorización desde una arquitectura procedural hacia una **arquitectura orientada a objetos basada en capas**. El proyecto implementa un sistema de comercio electrónico completo con autenticación JWT, gestión de usuarios, productos, carritos y pedidos.

---

## 🏗️ Arquitectura del Proyecto

### Estructura de Capas (Patrón en Implementación)

```
┌─────────────────────────────────────────┐
│         ROUTERS (API Layer)             │  ← Endpoints HTTP
├─────────────────────────────────────────┤
│         SERVICES (Business Logic)       │  ← Lógica de negocio
├─────────────────────────────────────────┤
│      REPOSITORIES (Data Access)         │  ← Acceso a datos
├─────────────────────────────────────────┤
│         MODELS (SQLAlchemy)             │  ← Modelos de BD
└─────────────────────────────────────────┘
```

### Directorio Principal: `backend_tienda/app/`

```
app/
├── core/                      # Configuración centralizada
│   ├── app.py                # Factory de aplicación FastAPI
│   ├── config.py             # Settings con Pydantic
│   └── dependencies.py       # Inyección de dependencias
│
├── repositories/             # Capa de acceso a datos (10 repositorios)
│   ├── base.py              # Clase base Repository
│   ├── usuario_repository.py
│   ├── cliente_repository.py
│   ├── categoria_repository.py
│   ├── producto_repository.py
│   ├── pedido_repository.py
│   ├── detalle_pedido_repository.py
│   ├── carrito_repository.py
│   ├── detalle_carrito_repository.py
│   └── audit_log_repository.py
│
├── services/                 # Capa de lógica de negocio (10 servicios)
│   ├── usuario_service.py
│   ├── cliente_service.py
│   ├── categoria_service.py
│   ├── producto_service.py
│   ├── pedido_service.py
│   ├── detalle_pedido_service.py
│   ├── carrito_service.py
│   ├── detalle_carrito_service.py
│   └── audit_log_service.py
│
├── routers/                  # Endpoints modulares (en desarrollo)
│
├── models.py                 # Modelos SQLAlchemy
├── schemas.py                # Esquemas Pydantic
├── crud.py                   # Funciones CRUD legacy
├── database.py               # Configuración de BD
├── auth.py                   # Autenticación JWT
├── email_service.py          # Servicio de emails
├── audit.py                  # Sistema de auditoría
└── main.py                   # Punto de entrada legacy
```

---

## 🔑 Componentes Principales

### 1. **Core (Configuración Centralizada)**

#### `core/config.py`
- Usa **Pydantic Settings** para gestión de configuración
- Variables de entorno centralizadas
- Configuración de SMTP, CORS, JWT, base de datos
- Patrón Singleton con `@lru_cache`

**Características destacadas:**
```python
class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "*"
    # SMTP Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
```

#### `core/dependencies.py`
- Inyección de dependencias para repositorios y servicios
- Gestión del ciclo de vida de la base de datos
- Proveedores de utilidades (email, auth)

### 2. **Repositories (Capa de Acceso a Datos)**

#### Patrón Repository
- **Clase base:** `Repository` en `base.py`
- Encapsula operaciones de SQLAlchemy
- Métodos comunes: `add()`, `commit()`, `rollback()`, `refresh()`

**Ejemplo: UsuarioRepository**
```python
class UsuarioRepository(Repository):
    def get(self, usuario_id: int) -> Optional[models.Usuario]
    def get_by_email(self, correo: str) -> Optional[models.Usuario]
    def create(self, usuario: schemas.UsuarioCreate) -> models.Usuario
    def update(self, usuario_id: int, usuario: schemas.UsuarioUpdate)
    def delete(self, usuario_id: int) -> Optional[models.Usuario]
```

**Ventajas:**
- Abstracción de la persistencia
- Reutilización de código
- Facilita testing con mocks
- Separación de responsabilidades

### 3. **Services (Capa de Lógica de Negocio)**

#### Patrón Service Layer
- Orquesta operaciones de negocio
- Valida reglas de negocio
- Coordina múltiples repositorios
- Maneja excepciones HTTP

**Ejemplo: UsuarioService**
```python
class UsuarioService:
    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository
    
    def autenticar_usuario(self, correo: str, contraseña: str)
    def crear_usuario(self, usuario: schemas.UsuarioCreate)
    def confirmar_cuenta(self, correo: str, pin: str)
    def actualizar_usuario(self, usuario_id: int, ...)
```

**Responsabilidades:**
- Validación de credenciales
- Envío de emails de confirmación
- Verificación de permisos
- Lógica de recuperación de contraseña

### 4. **Models (SQLAlchemy)**

Entidades principales:
- `Usuario` - Autenticación y roles
- `Cliente` - Perfil de cliente
- `Categoria` - Categorías de productos
- `Producto` - Catálogo de productos
- `Carrito` - Carritos de compra
- `DetalleCarrito` - Productos en carrito
- `Pedido` - Órdenes de compra
- `DetallePedido` - Productos en pedido
- `AuditLog` - Registro de auditoría

### 5. **Authentication & Security**

#### `auth.py`
- Hash de contraseñas con **bcrypt**
- Generación y verificación de tokens JWT
- Dependencias de autenticación
- Roles: `cliente`, `admin`, `super_admin`

**Funciones principales:**
```python
hash_password(password: str) -> str
verify_password(plain_password: str, hashed_password: str) -> bool
crear_token_de_acceso(data: dict, expires_delta: Optional[timedelta] = None) -> str
verificar_token(token: str) -> Optional[dict]
get_current_user(token: str = Depends(oauth2_scheme)) -> dict
```

### 6. **Email Service**

#### `email_service.py`
- Envío de emails de confirmación
- Emails de recuperación de contraseña
- Configuración SMTP
- Templates HTML personalizados

---

## 🧪 Estrategia de Testing

### Estructura de Pruebas: `tests/`

```
tests/
├── conftest.py              # Fixtures y configuración
├── test_auth.py             # Pruebas unitarias de autenticación
├── test_usuarios.py         # Pruebas de integración de usuarios
├── test_productos.py        # Pruebas de productos y categorías
├── test_carritos.py         # Pruebas de carritos
└── test_pedidos.py          # Pruebas de pedidos y clientes
```

### Configuración de Testing (`conftest.py`)

#### 1. **Base de Datos de Pruebas**
```python
# SQLite en memoria para pruebas
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
```

#### 2. **Fixtures Principales**

| Fixture | Descripción | Scope |
|---------|-------------|-------|
| `db_session` | Sesión de BD limpia por prueba | function |
| `client` | TestClient de FastAPI | function |
| `usuario_test` | Usuario de prueba verificado | function |
| `usuario_admin_test` | Usuario admin de prueba | function |
| `cliente_test` | Cliente con perfil completo | function |
| `categoria_test` | Categoría de prueba | function |
| `producto_test` | Producto de prueba | function |
| `token_test` | Token JWT de usuario | function |
| `token_admin_test` | Token JWT de admin | function |

#### 3. **Características de las Fixtures**

**Aislamiento por prueba:**
```python
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)  # Limpieza total
```

**Mock de servicios externos:**
```python
# Mock del servicio de email para evitar envíos reales
mock_email_service = MagicMock()
usuario_service_module.email_service = mock_email_service
```

**Inyección de dependencias en tests:**
```python
def override_get_db():
    try:
        yield db_session
    finally:
        pass

app.dependency_overrides[get_db] = override_get_db
```

### Tipos de Pruebas

#### 1. **Pruebas Unitarias** (`test_auth.py`)
- Testean funciones individuales
- Sin dependencias de BD
- Rápidas y aisladas

**Ejemplo:**
```python
class TestPasswordHashing:
    def test_hash_password(self):
        password = "test_password_123"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        password = "test_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
```

#### 2. **Pruebas de Integración** (resto de archivos)
- Testean endpoints completos
- Usan base de datos de prueba
- Verifican flujos end-to-end

**Ejemplo:**
```python
class TestLogin:
    def test_login_exitoso(self, client, usuario_test):
        response = client.post(
            "/login",
            json={
                "correo": usuario_test.correo,
                "contraseña": "password123"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
```

### Configuración de Pytest (`pytest.ini`)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v                          # Verbose
    --tb=short                  # Traceback corto
    --strict-markers            # Marcadores estrictos
    --disable-warnings          # Deshabilitar warnings
    --cov=app                   # Cobertura del código
    --cov-report=term-missing   # Reporte en terminal
    --cov-report=html           # Reporte HTML
```

### Cobertura de Pruebas por Módulo

| Módulo | Archivo de Test | Casos de Prueba | Cobertura |
|--------|----------------|-----------------|-----------|
| **Autenticación** | `test_auth.py` | 10 pruebas | Hash, JWT, tokens |
| **Usuarios** | `test_usuarios.py` | 11 pruebas | Login, CRUD, permisos |
| **Productos** | `test_productos.py` | 9 pruebas | CRUD, categorías |
| **Carritos** | `test_carritos.py` | 8 pruebas | Crear, agregar, eliminar |
| **Pedidos** | `test_pedidos.py` | 10 pruebas | Crear, inventario, detalles |

**Total: ~48 pruebas automatizadas**

---

## 📊 Análisis de la Estrategia de Testing

### ✅ Fortalezas

1. **Aislamiento Completo**
   - Cada prueba tiene su propia BD en memoria
   - Limpieza automática después de cada test
   - No hay contaminación entre pruebas

2. **Fixtures Bien Diseñadas**
   - Reutilizables y componibles
   - Scope adecuado (`function`)
   - Mock de servicios externos

3. **Cobertura de Casos Críticos**
   - Casos exitosos (happy path)
   - Casos de error (validaciones)
   - Casos de permisos (autorización)

4. **Uso de la Nueva Arquitectura**
   - Las fixtures usan servicios y repositorios
   - Promueve el uso de la capa de servicios
   - Facilita la migración del código legacy

5. **Configuración Profesional**
   - Pytest configurado correctamente
   - Reportes de cobertura
   - Variables de entorno para tests

### ⚠️ Áreas de Mejora

1. **Falta de Pruebas Unitarias de Servicios**
   - Actualmente solo hay pruebas de integración
   - Deberían existir tests unitarios para cada servicio
   - Ejemplo: `test_usuario_service.py` con mocks de repositorios

2. **Cobertura de Casos Edge**
   - Faltan pruebas de concurrencia
   - Pruebas de límites (cantidades máximas, etc.)
   - Pruebas de rendimiento

3. **Testing de Email Service**
   - Se mockea pero no se verifica el contenido
   - Deberían verificarse los parámetros del mock

4. **Falta de Pruebas de Auditoría**
   - No hay tests para el sistema de auditoría
   - Debería verificarse que se registran las acciones

5. **Documentación de Tests**
   - Algunos tests podrían tener docstrings más descriptivos
   - Falta documentación de la estrategia de testing

---

## 🎯 Metodología de Testing Aplicada

### 1. **Arrange-Act-Assert (AAA)**

Todas las pruebas siguen este patrón:

```python
def test_crear_producto_exitoso(self, client, categoria_test, token_admin_test):
    # ARRANGE - Preparar datos
    producto_data = {
        "id_categoria": categoria_test.id_categoria,
        "nombre": "Laptop",
        "precio": 1299.99
    }
    
    # ACT - Ejecutar acción
    response = client.post(
        "/productos/",
        json=producto_data,
        headers=get_auth_headers(token_admin_test)
    )
    
    # ASSERT - Verificar resultado
    assert response.status_code == 200
    assert response.json()["nombre"] == "Laptop"
```

### 2. **Test Pyramid**

```
        /\
       /  \      E2E (Pocos)
      /____\     
     /      \    Integration (Moderados) ← AQUÍ ESTÁ EL FOCO
    /________\   
   /          \  Unit (Muchos) ← FALTA MÁS COBERTURA
  /____________\ 
```

**Estado actual:** Más pruebas de integración que unitarias

### 3. **Given-When-Then (BDD implícito)**

Los nombres de las pruebas siguen un patrón descriptivo:

```python
# Given: un usuario autenticado
# When: intenta crear un producto
# Then: el producto se crea exitosamente
def test_crear_producto_exitoso(...)

# Given: un usuario sin token
# When: intenta acceder a /usuarios/me
# Then: recibe un 401
def test_get_usuarios_me_sin_token(...)
```

### 4. **Fixtures como Factory Pattern**

Las fixtures actúan como factories de objetos de prueba:

```python
@pytest.fixture
def producto_test(db_session, categoria_test):
    """Factory de productos de prueba"""
    producto_service = ProductoService(ProductoRepository(db_session))
    return producto_service.crear_producto(ProductoCreate(...))
```

---

## 🔍 Comparación con Casos de Prueba Documentados

Según `TESTS_CONTEXT.md`, hay 16 casos de prueba backend definidos. Veamos la cobertura:

| ID | Caso de Prueba | Estado | Archivo |
|----|----------------|--------|---------|
| CP-001 | Registro de nuevo usuario | ✅ Cubierto | `test_usuarios.py::test_crear_usuario_exitoso` |
| CP-002 | Inicio de sesión | ✅ Cubierto | `test_usuarios.py::test_login_exitoso` |
| CP-004 | Añadir producto al carrito | ✅ Cubierto | `test_carritos.py::test_crear_detalle_carrito_exitoso` |
| CP-005 | Crear pedido y finalizar compra | ✅ Cubierto | `test_pedidos.py::test_crear_pedido_exitoso` |
| CP-007 | Validar campo obligatorio en registro | ✅ Cubierto | `test_usuarios.py::test_login_datos_faltantes` |
| CP-008 | Suma de productos en el carrito | ⚠️ Parcial | Falta test específico de suma |
| CP-009 | Proceso completo de compra | ❌ Falta | Flujo end-to-end completo |
| CP-011 | Validación de email en registro | ⚠️ Parcial | `test_usuarios.py::test_crear_usuario_datos_invalidos` |
| CP-012 | Validación de contraseña mínima | ❌ Falta | No hay validación de longitud |
| CP-013 | Cálculo de total del pedido | ✅ Cubierto | `test_pedidos.py::test_crear_detalle_pedido_exitoso` |
| CP-014 | Eliminación lógica de productos | ✅ Cubierto | `test_productos.py::test_eliminar_producto_exitoso` |
| CP-015 | Suma de stock al agregar producto | ❌ Falta | No hay test de inventario |
| CP-016 | Agregar producto repetido al carrito | ❌ Falta | No hay test de duplicados |
| CP-017 | Eliminar producto del carrito | ✅ Cubierto | `test_carritos.py::test_eliminar_detalle_carrito_exitoso` |
| CP-019 | Generación de email de confirmación | ⚠️ Mockeado | Se mockea pero no se verifica |
| CP-020 | Búsqueda por texto parcial | ❌ Falta | No hay tests de búsqueda |
| CP-021 | Búsqueda sin coincidencias | ❌ Falta | No hay tests de búsqueda |

**Resumen:**
- ✅ Cubiertos: 9/17 (53%)
- ⚠️ Parcialmente cubiertos: 3/17 (18%)
- ❌ Faltantes: 5/17 (29%)

---

## 💡 Recomendaciones

### 1. **Completar Casos de Prueba Faltantes**

Crear tests para:
- CP-009: Flujo completo de compra (usuario → carrito → pedido)
- CP-012: Validación de contraseña mínima
- CP-015: Gestión de inventario al agregar productos
- CP-016: Productos duplicados en carrito
- CP-020/021: Búsqueda de productos

### 2. **Agregar Pruebas Unitarias de Servicios**

```python
# tests/unit/test_usuario_service.py
class TestUsuarioService:
    def test_crear_usuario_correo_duplicado(self):
        # Mock del repositorio
        mock_repo = MagicMock()
        mock_repo.get_by_email.return_value = Usuario(...)
        
        service = UsuarioService(mock_repo)
        
        with pytest.raises(HTTPException) as exc:
            service.crear_usuario(UsuarioCreate(...))
        
        assert exc.value.status_code == 400
```

### 3. **Mejorar Verificación de Emails**

```python
def test_envio_email_confirmacion(self, client, mock_email_service):
    response = client.post("/usuarios/", json={...})
    
    # Verificar que se llamó al servicio de email
    mock_email_service.enviar_email_confirmacion.assert_called_once()
    
    # Verificar parámetros
    call_args = mock_email_service.enviar_email_confirmacion.call_args
    assert call_args[1]["destinatario"] == "test@example.com"
```

### 4. **Agregar Tests de Auditoría**

```python
def test_auditoria_creacion_usuario(self, db_session, client):
    response = client.post("/usuarios/", json={...})
    
    # Verificar que se creó un registro de auditoría
    audit_logs = db_session.query(AuditLog).all()
    assert len(audit_logs) == 1
    assert audit_logs[0].accion == "crear_usuario"
```

### 5. **Implementar Tests de Carga**

```python
# tests/performance/test_load.py
import pytest
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def get_productos(self):
        self.client.get("/productos/")
```

### 6. **Documentar Estrategia de Testing**

Crear `tests/README.md` con:
- Cómo ejecutar las pruebas
- Estructura de fixtures
- Convenciones de nombres
- Cómo agregar nuevas pruebas

---

## 📈 Métricas de Calidad

### Cobertura de Código
```bash
pytest --cov=app --cov-report=html
```

**Objetivo:** >80% de cobertura

### Ejecución de Tests
```bash
# Todas las pruebas
pytest

# Pruebas específicas
pytest tests/test_auth.py

# Con verbose
pytest -v

# Solo pruebas que fallan
pytest --lf
```

---

## 🎓 Conclusiones

### Puntos Fuertes del Backend

1. **Arquitectura Sólida**
   - Separación clara de responsabilidades
   - Patrón Repository bien implementado
   - Servicios con lógica de negocio encapsulada

2. **Testing Bien Estructurado**
   - Fixtures reutilizables
   - Aislamiento de pruebas
   - Mock de servicios externos

3. **Seguridad**
   - JWT implementado correctamente
   - Hash de contraseñas con bcrypt
   - Sistema de roles y permisos

4. **Configuración Profesional**
   - Variables de entorno centralizadas
   - Inyección de dependencias
   - Sistema de auditoría

### Áreas de Oportunidad

1. **Completar Migración a OOP**
   - Terminar de migrar routers
   - Eliminar código legacy de `crud.py`
   - Documentar la nueva arquitectura

2. **Ampliar Cobertura de Tests**
   - Agregar pruebas unitarias de servicios
   - Completar casos de prueba faltantes
   - Tests de rendimiento

3. **Mejorar Documentación**
   - Documentar estrategia de testing
   - Agregar ejemplos de uso
   - Documentar API con OpenAPI

4. **Optimización**
   - Implementar caché
   - Optimizar queries de BD
   - Agregar paginación en todos los endpoints

---

## 📚 Recursos y Referencias

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Pytest Docs:** https://docs.pytest.org/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **Pydantic Docs:** https://docs.pydantic.dev/

---

**Fecha de Análisis:** Noviembre 2025  
**Versión del Backend:** En refactorización (OOP)  
**Estado:** En desarrollo activo
