"""
FastAPI application entry point.

- Defines the application, routes, and dependency injection for the backend API.
- Configures CORS and the database connection.
- Main dependencies: FastAPI, SQLAlchemy, local modules (models, schemas, crud, auth, database)
"""

import os
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from . import models
from .database import engine
from .audit import set_audit_context, clear_audit_context
from .auth import verificar_token
from .routers import (
    usuarios, 
    clientes, 
    categorias, 
    productos, 
    pedidos, 
    detalle_pedidos, 
    carritos, 
    detalle_carritos, 
    audit
)

# Cargar variables de entorno
load_dotenv()

# En producción, usar migraciones de Alembic en lugar de create_all()
# Solo crear tablas automáticamente en desarrollo si no hay migraciones
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
if ENVIRONMENT == "development":
    # Solo en desarrollo: crear tablas si no existen
    # En producción, siempre usar: alembic upgrade head
    try:
        # Verificar si existe la tabla de versiones de Alembic
        from sqlalchemy import inspect
        inspector = inspect(engine)
        if "alembic_version" not in inspector.get_table_names():
            # Si no hay migraciones, crear tablas (solo desarrollo)
            models.Base.metadata.create_all(bind=engine)
            print("Advertencia: Tablas creadas automáticamente. En producción, usa 'alembic upgrade head'")
    except Exception as e:
        print(f"Advertencia: No se pudieron crear las tablas automáticamente: {e}")
        print("En producción, asegúrate de ejecutar: alembic upgrade head")

# Importar audit para registrar los event listeners
from . import audit  # noqa: F401

# Configuración de metadatos para Swagger/OpenAPI
tags_metadata = [
    {
        "name": "Sistema",
        "description": "Endpoints del sistema: health check e información general.",
    },
    {
        "name": "Autenticación",
        "description": "Endpoints para registro, login y gestión de sesiones. Incluye confirmación de cuenta y recuperación de contraseña.",
    },
    {
        "name": "Usuarios",
        "description": "Gestión de usuarios. Solo administradores pueden listar, actualizar o eliminar usuarios.",
    },
    {
        "name": "Clientes",
        "description": "Gestión de perfiles de clientes. Los clientes pueden gestionar su propio perfil.",
    },
    {
        "name": "Categorías",
        "description": "Gestión de categorías de productos. Las categorías son públicas para lectura, pero solo administradores pueden modificarlas.",
    },
    {
        "name": "Productos",
        "description": "Gestión de productos del catálogo. Los productos son públicos para lectura, pero solo administradores pueden modificarlos.",
    },
    {
        "name": "Pedidos",
        "description": "Gestión de pedidos. Los clientes pueden crear y ver sus propios pedidos, los administradores tienen acceso completo.",
    },
    {
        "name": "Carritos",
        "description": "Gestión de carritos de compra. Los clientes pueden gestionar sus propios carritos.",
    },
    {
        "name": "Auditoría",
        "description": "Logs de auditoría del sistema. Solo accesible para administradores.",
    },
]

app = FastAPI(
    title="API Rosaline Bakery",
    description="""
    API REST para la tienda online de Rosaline Bakery.
    
    ## Características
    
    * **Autenticación JWT**: Sistema de autenticación basado en tokens JWT
    * **Roles**: Sistema de roles (cliente, admin, super_admin)
    * **Auditoría**: Registro completo de cambios en la base de datos
    * **Confirmación de email**: Sistema de verificación de cuentas
    * **Recuperación de contraseña**: Sistema de recuperación mediante PIN
    
    ## Autenticación
    
    La mayoría de los endpoints requieren autenticación. Para autenticarte:
    
    1. Registra un usuario en `/usuarios/`
    2. Confirma tu cuenta con el token recibido por email
    3. Inicia sesión en `/login` para obtener un token JWT
    4. Usa el token en el header: `Authorization: Bearer <token>`
    
    ## Permisos
    
    * **Público**: Catálogo (productos, categorías), registro, login
    * **Cliente**: Gestión de su propio perfil, pedidos y carritos
    * **Admin**: Acceso completo a todos los recursos
    """,
    version="1.0.0",
    contact={
        "name": "Soporte Rosaline Bakery",
        "email": "soporte@rosalinebakery.com",
    },
    license_info={
        "name": "Proprietary",
    },
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configurar CORS desde variables de entorno
# Por defecto permite todos los orígenes para desarrollo
# En producción, configurar CORS_ORIGINS con los orígenes específicos del frontend
CORS_ORIGINS_ENV = os.getenv("CORS_ORIGINS", "*")
if CORS_ORIGINS_ENV == "*" or CORS_ORIGINS_ENV == "":
    CORS_ORIGINS = ["*"]
    # Cuando se usa "*", no se pueden usar credenciales (restricción de CORS)
    ALLOW_CREDENTIALS = False
else:
    CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_ENV.split(",")]
    # Con orígenes específicos, se pueden usar credenciales
    ALLOW_CREDENTIALS = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar esquema de seguridad para Swagger
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=tags_metadata,
    )
    
    # Agregar esquema de seguridad JWT
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Ingresa el token JWT obtenido del endpoint /login. Formato: Bearer <token>"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Maneja errores de validación de Pydantic y retorna mensajes claros.
    Asegura que los headers CORS se incluyan incluso en errores de validación.
    """
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"] if loc != "body")
        message = error["msg"]
        error_type = error["type"]
        
        # Mejorar mensajes de error comunes
        if error_type == "value_error.missing":
            message = f"El campo '{field}' es requerido"
        elif error_type == "value_error.email":
            message = f"'{field}' debe ser un correo electrónico válido"
        elif error_type == "value_error.str.regex":
            message = f"'{field}' tiene un formato inválido"
        elif error_type == "type_error.integer":
            message = f"'{field}' debe ser un número entero"
        elif error_type == "type_error.float":
            message = f"'{field}' debe ser un número decimal"
        
        errors.append({
            "field": field,
            "message": message,
            "type": error_type
        })
    
    # Obtener el origen de la request para CORS
    origin = request.headers.get("origin")
    headers = {}
    
    # Si hay un origen y está en la lista permitida, agregar headers CORS
    if origin:
        if CORS_ORIGINS == ["*"]:
            headers["Access-Control-Allow-Origin"] = "*"
        elif origin in CORS_ORIGINS:
            headers["Access-Control-Allow-Origin"] = origin
            if ALLOW_CREDENTIALS:
                headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Methods"] = "*"
        headers["Access-Control-Allow-Headers"] = "*"
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Error de validación",
            "errors": errors,
            "message": f"Se encontraron {len(errors)} error(es) de validación"
        },
        headers=headers
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Maneja excepciones no controladas y retorna un error genérico.
    Asegura que los headers CORS se incluyan incluso en errores.
    """
    import traceback
    print(f"Error no controlado: {exc}")
    print(traceback.format_exc())
    
    # Obtener el origen de la request para CORS
    origin = request.headers.get("origin")
    headers = {}
    
    # Si hay un origen y está en la lista permitida, agregar headers CORS
    if origin:
        if CORS_ORIGINS == ["*"]:
            headers["Access-Control-Allow-Origin"] = "*"
        elif origin in CORS_ORIGINS:
            headers["Access-Control-Allow-Origin"] = origin
            if ALLOW_CREDENTIALS:
                headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Methods"] = "*"
        headers["Access-Control-Allow-Headers"] = "*"
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor",
            "message": "Ha ocurrido un error inesperado. Por favor, intenta más tarde."
        },
        headers=headers
    )

@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Middleware para capturar contexto de auditoría."""
    # Limpiar contexto anterior
    clear_audit_context()
    
    # Obtener información de la request
    ip_address = request.client.host if request.client else None
    endpoint = f"{request.method} {request.url.path}"
    
    # Intentar obtener usuario del token si existe
    user_id = None
    user_email = None
    
    try:
        # Solo si el endpoint requiere autenticación
        if request.url.path not in ["/login", "/usuarios/", "/docs", "/openapi.json", "/redoc", "/", "/health"]:
            auth_header = request.headers.get("authorization")
            if auth_header:
                token = auth_header.replace("Bearer ", "")
                payload = verificar_token(token)
                if payload:
                    user_id = payload.get("id_usuario")
                    user_email = payload.get("sub")
    except:
        pass  # Si falla, continuar sin contexto de usuario
    
    # Establecer contexto
    set_audit_context(
        user_id=user_id,
        user_email=user_email,
        ip_address=ip_address,
        endpoint=endpoint
    )
    
    # Continuar con la request
    response = await call_next(request)
    
    # Limpiar contexto después de la request
    clear_audit_context()
    
    return response

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Inclusión de routers
app.include_router(usuarios.router)
app.include_router(usuarios.auth_router)
app.include_router(clientes.router)
app.include_router(categorias.router)
app.include_router(productos.router)
app.include_router(pedidos.router)
app.include_router(detalle_pedidos.router)
app.include_router(carritos.router)
app.include_router(detalle_carritos.router)
app.include_router(audit.router)

@app.get("/", tags=["Sistema"], summary="Información del API")
def root():
    return {
        "status": "ok",
        "message": "API funcionando correctamente",
        "service": "backend-tienda",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["Sistema"], summary="Health Check")
def health_check():
    return {
        "status": "healthy",
        "service": "backend-tienda"
    }
