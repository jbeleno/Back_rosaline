"""
FastAPI application entry point.

- Defines the application, routes, and dependency injection for the backend API.
- Configures CORS and the database connection.
- Main dependencies: FastAPI, SQLAlchemy, local modules (models, schemas, crud, auth, database)
"""

import os
from fastapi import FastAPI, Depends, HTTPException, Body, Request, Query, Path, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime
from . import models, schemas, crud
from .database import SessionLocal, engine
from .auth import crear_token_de_acceso, get_current_user, verify_password, require_admin, require_super_admin, require_cliente_or_admin, verify_resource_owner, verificar_token
from .audit import set_audit_context, clear_audit_context

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
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Error de validación",
            "errors": errors,
            "message": f"Se encontraron {len(errors)} error(es) de validación"
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Maneja excepciones no controladas y retorna un error genérico.
    """
    import traceback
    print(f"Error no controlado: {exc}")
    print(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor",
            "message": "Ha ocurrido un error inesperado. Por favor, intenta más tarde."
        }
    )

@app.get("/", tags=["Sistema"], summary="Información del API", response_description="Información básica del servicio")
def root():
    """
    Endpoint raíz para verificar que el servidor está funcionando.
    
    Retorna información básica sobre el API y enlaces a la documentación.
    """
    return {
        "status": "ok",
        "message": "API funcionando correctamente",
        "service": "backend-tienda",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["Sistema"], summary="Health Check", response_description="Estado de salud del servicio")
def health_check():
    """
    Endpoint de health check para monitoreo.
    
    Útil para verificar que el servicio está en funcionamiento.
    """
    return {
        "status": "healthy",
        "service": "backend-tienda"
    }

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

@app.post(
    "/usuarios/", 
    tags=["Autenticación"],
    summary="Registrar nuevo usuario",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.Usuario,
    responses={
        201: {"description": "Usuario creado exitosamente"},
        400: {"description": "El correo ya está registrado"},
        422: {"description": "Error de validación"}
    }
)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo usuario y envía email de confirmación con PIN.
    
    **Importante**: Después de registrarte, recibirás un PIN de 6 dígitos por email.
    Ingresa este PIN en la misma página de registro para confirmar tu cuenta.
    
    El usuario se crea con rol "cliente" por defecto.
    """
    db_usuario = crud.get_usuario_por_correo(db, correo=usuario.correo)
    if db_usuario:
        raise HTTPException(status_code=400, detail="Correo ya registrado")
    
    nuevo_usuario = crud.crear_usuario(db=db, usuario=usuario)
    
    # Enviar email de confirmación con PIN
    from . import email_service
    # Obtener nombre del usuario si tiene perfil de cliente
    nombre = usuario.correo.split("@")[0]  # Usar parte del email como nombre temporal
    cliente = crud.get_cliente_por_id_usuario(db, nuevo_usuario.id_usuario)
    if cliente:
        nombre = f"{cliente.nombre} {cliente.apellido}"
    
    email_service.enviar_email_confirmacion(
        destinatario=nuevo_usuario.correo,
        nombre=nombre,
        pin=nuevo_usuario.token_confirmacion
    )
    
    return nuevo_usuario

@app.post(
    "/clientes/",
    tags=["Clientes"],
    summary="Crear cliente",
    response_model=schemas.Cliente,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Cliente creado exitosamente"},
        403: {"description": "No tienes permisos para crear este perfil"},
        401: {"description": "No autenticado"}
    }
)
def crear_cliente(
    cliente: schemas.ClienteCreate, 
    current_user: dict = Depends(require_cliente_or_admin()),
    db: Session = Depends(get_db)
):
    """
    Crear perfil de cliente.
    
    - Los clientes solo pueden crear su propio perfil.
    - Los administradores pueden crear cualquier perfil.
    """
    # Validar que el cliente solo pueda crear su propio perfil
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    if user_role not in ["admin", "super_admin"] and cliente.id_usuario != user_id:
        raise HTTPException(
            status_code=403, 
            detail="Solo puedes crear tu propio perfil de cliente"
        )
    
    return crud.crear_cliente(db=db, cliente=cliente)

@app.get(
    "/clientes/",
    tags=["Clientes"],
    summary="Listar clientes",
    response_model=list[schemas.Cliente],
    responses={
        200: {"description": "Lista de clientes"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo administradores"}
    }
)
def listar_clientes(
    skip: int = Query(0, ge=0, description="Número de registros a saltar (paginación)"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros a retornar"),
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Lista todos los clientes.
    
    **Solo accesible para administradores.**
    """
    return crud.get_clientes(db, skip=skip, limit=limit)

@app.get(
    "/clientes/usuario/{id_usuario}",
    tags=["Clientes"],
    summary="Obtener cliente por ID de usuario",
    response_model=schemas.Cliente,
    responses={
        200: {"description": "Cliente encontrado"},
        404: {"description": "Cliente no encontrado"},
        403: {"description": "No tienes permisos para ver este perfil"},
        401: {"description": "No autenticado"}
    }
)
def obtener_cliente_por_usuario(
    id_usuario: int = Path(..., description="ID del usuario"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el perfil de cliente por ID de usuario.
    
    - Los clientes solo pueden ver su propio perfil.
    - Los administradores pueden ver cualquier perfil.
    """
    # Validar propiedad del recurso
    verify_resource_owner(id_usuario, current_user)
    
    cliente = crud.get_cliente_por_id_usuario(db, id_usuario)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@app.get(
    "/clientes/{cliente_id}",
    tags=["Clientes"],
    summary="Obtener cliente por ID",
    response_model=schemas.Cliente,
    responses={
        200: {"description": "Cliente encontrado"},
        404: {"description": "Cliente no encontrado"},
        403: {"description": "No tienes permisos para ver este perfil"},
        401: {"description": "No autenticado"}
    }
)
def obtener_cliente(
    cliente_id: int = Path(..., description="ID del cliente"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene un cliente específico por ID.
    
    - Los clientes solo pueden ver su propio perfil.
    - Los administradores pueden ver cualquier perfil.
    """
    cliente = crud.get_cliente(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Validar propiedad del recurso
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    if user_role not in ["admin", "super_admin"] and cliente.id_usuario != user_id:
        raise HTTPException(
            status_code=403,
            detail="Solo puedes ver tu propio perfil"
        )
    
    return cliente

@app.post(
    "/categorias/",
    tags=["Categorías"],
    summary="Crear categoría",
    response_model=schemas.Categoria,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Categoría creada exitosamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo administradores"}
    }
)
def crear_categoria(
    categoria: schemas.CategoriaCreate, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Crea una nueva categoría de productos.
    
    **Solo accesible para administradores.**
    """
    return crud.crear_categoria(db=db, categoria=categoria)

@app.get(
    "/categorias/",
    tags=["Categorías"],
    summary="Listar categorías",
    response_model=list[schemas.Categoria],
    description="Endpoint público. No requiere autenticación."
)
def listar_categorias(
    skip: int = Query(0, ge=0, description="Número de registros a saltar (paginación)"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros a retornar"),
    db: Session = Depends(get_db)
):
    """
    Lista todas las categorías de productos disponibles.
    
    Este endpoint es **público** y no requiere autenticación.
    """
    return crud.get_categorias(db, skip=skip, limit=limit)

@app.get(
    "/categorias/{categoria_id}",
    tags=["Categorías"],
    summary="Obtener categoría por ID",
    response_model=schemas.Categoria,
    description="Endpoint público. No requiere autenticación.",
    responses={
        200: {"description": "Categoría encontrada"},
        404: {"description": "Categoría no encontrada"}
    }
)
def obtener_categoria(
    categoria_id: int = Path(..., description="ID de la categoría"),
    db: Session = Depends(get_db)
):
    """
    Obtiene una categoría específica por ID.
    
    Este endpoint es **público** y no requiere autenticación.
    """
    categoria = crud.get_categoria(db, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria

@app.post(
    "/productos/",
    tags=["Productos"],
    summary="Crear producto",
    response_model=schemas.Producto,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Producto creado exitosamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo administradores"}
    }
)
def crear_producto(
    producto: schemas.ProductoCreate, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo producto en el catálogo.
    
    **Solo accesible para administradores.**
    """
    return crud.crear_producto(db=db, producto=producto)

@app.get(
    "/productos/",
    tags=["Productos"],
    summary="Listar productos",
    response_model=list[schemas.Producto],
    description="Endpoint público. No requiere autenticación."
)
def listar_productos(
    skip: int = Query(0, ge=0, description="Número de registros a saltar (paginación)"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros a retornar"),
    db: Session = Depends(get_db)
):
    """
    Lista todos los productos disponibles en el catálogo.
    
    Este endpoint es **público** y no requiere autenticación.
    """
    return crud.get_productos(db, skip=skip, limit=limit)

@app.get(
    "/productos/{producto_id}",
    tags=["Productos"],
    summary="Obtener producto por ID",
    response_model=schemas.Producto,
    description="Endpoint público. No requiere autenticación.",
    responses={
        200: {"description": "Producto encontrado"},
        404: {"description": "Producto no encontrado"}
    }
)
def obtener_producto(
    producto_id: int = Path(..., description="ID del producto"),
    db: Session = Depends(get_db)
):
    """
    Obtiene un producto específico por ID.
    
    Este endpoint es **público** y no requiere autenticación.
    """
    producto = crud.get_producto(db, producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@app.post(
    "/pedidos/",
    tags=["Pedidos"],
    summary="Crear pedido",
    response_model=schemas.Pedido,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Pedido creado exitosamente"},
        403: {"description": "Solo puedes crear pedidos para tu propia cuenta"},
        401: {"description": "No autenticado"}
    }
)
def crear_pedido(
    pedido: schemas.PedidoCreate, 
    current_user: dict = Depends(require_cliente_or_admin()),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo pedido.
    
    - Los clientes solo pueden crear pedidos para sí mismos.
    - Los administradores pueden crear pedidos para cualquier cliente.
    """
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar que el cliente solo pueda crear pedidos para sí mismo
    if user_role not in ["admin", "super_admin"]:
        cliente = crud.get_cliente(db, pedido.id_cliente)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        if cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes crear pedidos para tu propia cuenta"
            )
    
    return crud.crear_pedido(db=db, pedido=pedido)

@app.get(
    "/pedidos/",
    tags=["Pedidos"],
    summary="Listar todos los pedidos",
    response_model=list[schemas.Pedido],
    responses={
        200: {"description": "Lista de pedidos"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo administradores"}
    }
)
def listar_pedidos(
    skip: int = Query(0, ge=0, description="Número de registros a saltar (paginación)"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros a retornar"),
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Lista todos los pedidos del sistema.
    
    **Solo accesible para administradores.**
    """
    return crud.get_pedidos(db, skip=skip, limit=limit)

@app.post(
    "/detalle_pedidos/",
    tags=["Pedidos"],
    summary="Crear detalle de pedido",
    response_model=schemas.DetallePedido,
    status_code=status.HTTP_201_CREATED
)
def crear_detalle_pedido(
    detalle: schemas.DetallePedidoCreate, 
    current_user: dict = Depends(require_cliente_or_admin()),
    db: Session = Depends(get_db)
):
    """
    Crear detalle de pedido. Los clientes solo pueden agregar detalles a sus propios pedidos.
    Los administradores pueden agregar detalles a cualquier pedido.
    """
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar que el pedido pertenezca al usuario si es cliente
    if user_role not in ["admin", "super_admin"]:
        pedido = crud.get_pedido(db, detalle.id_pedido)
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        cliente = crud.get_cliente(db, pedido.id_cliente)
        if not cliente or cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes agregar detalles a tus propios pedidos"
            )
    
    return crud.crear_detalle_pedido(db=db, detalle=detalle)

@app.get(
    "/detalle_pedidos/",
    tags=["Pedidos"],
    summary="Listar detalles de pedidos",
    response_model=list[schemas.DetallePedido]
)
def listar_detalles_pedido(
    skip: int = 0, 
    limit: int = 100, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Listar todos los detalles de pedidos. Solo accesible para administradores."""
    return crud.get_detalles_pedido(db, skip=skip, limit=limit)

@app.get(
    "/usuarios/",
    tags=["Usuarios"],
    summary="Listar usuarios",
    response_model=list[schemas.Usuario],
    responses={
        200: {"description": "Lista de usuarios"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo administradores"}
    }
)
def listar_usuarios(
    skip: int = Query(0, ge=0, description="Número de registros a saltar (paginación)"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros a retornar"),
    rol: Optional[str] = Query(None, description="Filtrar por rol (cliente, admin, super_admin)"),
    correo: Optional[str] = Query(None, description="Filtrar por correo (búsqueda parcial)"),
    email_verificado: Optional[str] = Query(None, description="Filtrar por estado de verificación (S, N)"),
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Lista todos los usuarios con filtros opcionales y paginación.
    
    **Solo accesible para administradores.**
    
    Los administradores pueden ver todos los usuarios, incluyendo otros administradores,
    pero no pueden modificar o eliminar a otros administradores.
    
    Filtros disponibles:
    - **rol**: Filtrar por rol (cliente, admin, super_admin)
    - **correo**: Búsqueda parcial por correo electrónico
    - **email_verificado**: Filtrar por estado de verificación (S, N)
    """
    return crud.get_usuarios(
        db=db,
        skip=skip,
        limit=limit,
        rol=rol,
        correo=correo,
        email_verificado=email_verificado
    )

@app.put(
    "/usuarios/{usuario_id}",
    tags=["Usuarios"],
    summary="Actualizar usuario",
    response_model=schemas.Usuario,
    responses={
        200: {"description": "Usuario actualizado exitosamente"},
        404: {"description": "Usuario no encontrado"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo administradores o no puedes modificar a otro administrador"}
    }
)
def actualizar_usuario(
    usuario_id: int = Path(..., description="ID del usuario"),
    usuario: schemas.UsuarioUpdate = Body(...), 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Actualiza un usuario existente.
    
    **Solo accesible para administradores o super administradores.**
    
    **Restricciones**:
    - **Admin**: 
      - Puede modificar su propia cuenta
      - Puede modificar usuarios con rol "cliente"
      - NO puede modificar a otros administradores o super administradores
      - NO puede modificar email_verificado
    - **Super Admin**:
      - Puede modificar a todos los usuarios (admin, super_admin, cliente)
      - Puede modificar email_verificado (útil para correos genéricos)
      - NO puede cambiar su propio rol (debe mantener "super_admin")
    
    **Nota**: Todos los campos son opcionales. Solo se actualizarán los campos que se proporcionen en el body.
    """
    # Obtener el usuario a modificar
    db_usuario = crud.get_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    current_user_id = current_user.get("id_usuario")
    current_user_role = current_user.get("rol")
    es_super_admin = current_user_role == "super_admin"
    
    # Validar que admin no intente modificar email_verificado
    if not es_super_admin and usuario.email_verificado is not None:
        raise HTTPException(
            status_code=403,
            detail="Solo los super administradores pueden modificar el estado de verificación de email"
        )
    
    # Validar restricciones para super_admin
    if es_super_admin:
        # Super admin puede modificar a todos, pero no puede cambiar su propio rol
        if usuario_id == current_user_id and usuario.rol is not None and usuario.rol != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="No puedes cambiar tu propio rol. Los super administradores deben mantener su rol."
            )
    # Validar restricciones para admin
    elif current_user_role == "admin":
        # Admin no puede modificar a otros admins o super_admins
        if db_usuario.rol in ["admin", "super_admin"] and db_usuario.id_usuario != current_user_id:
            raise HTTPException(
                status_code=403,
                detail="No puedes modificar a otro administrador o super administrador. Solo puedes modificar tu propia cuenta o usuarios con rol 'cliente'"
            )
    
    return crud.actualizar_usuario(db, usuario_id, usuario, es_super_admin=es_super_admin)

@app.delete(
    "/usuarios/{usuario_id}",
    tags=["Usuarios"],
    summary="Eliminar usuario",
    response_model=schemas.Usuario,
    responses={
        200: {"description": "Usuario eliminado exitosamente"},
        404: {"description": "Usuario no encontrado"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo administradores o no puedes eliminar a otro administrador"}
    }
)
def eliminar_usuario(
    usuario_id: int = Path(..., description="ID del usuario"),
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Elimina un usuario del sistema.
    
    **Solo accesible para administradores o super administradores.**
    
    **Restricciones**:
    - **Admin**: 
      - Puede eliminar usuarios con rol "cliente"
      - NO puede eliminar a otros administradores o super administradores
      - NO puede eliminarse a sí mismo
    - **Super Admin**:
      - Puede eliminar a todos los usuarios (admin, super_admin, cliente)
      - NO puede eliminarse a sí mismo
    """
    # Obtener el usuario a eliminar
    db_usuario = crud.get_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    current_user_id = current_user.get("id_usuario")
    current_user_role = current_user.get("rol")
    
    # Nadie puede eliminarse a sí mismo
    if usuario_id == current_user_id:
        raise HTTPException(
            status_code=403,
            detail="No puedes eliminarte a ti mismo"
        )
    
    # Validar restricciones para admin
    if current_user_role == "admin":
        # Admin no puede eliminar a otros admins o super_admins
        if db_usuario.rol in ["admin", "super_admin"]:
            raise HTTPException(
                status_code=403,
                detail="No puedes eliminar a otro administrador o super administrador. Solo puedes eliminar usuarios con rol 'cliente'"
            )
    
    # Super admin puede eliminar a todos (excepto a sí mismo, ya validado arriba)
    return crud.eliminar_usuario(db, usuario_id)

@app.put(
    "/clientes/{cliente_id}",
    tags=["Clientes"],
    summary="Actualizar cliente",
    response_model=schemas.Cliente
)
def actualizar_cliente(
    cliente_id: int, 
    cliente: schemas.ClienteCreate, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar cliente. Los clientes solo pueden actualizar su propio perfil.
    Los administradores pueden actualizar cualquier perfil.
    """
    db_cliente = crud.get_cliente(db, cliente_id)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Validar propiedad del recurso
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    if user_role not in ["admin", "super_admin"] and db_cliente.id_usuario != user_id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para actualizar este cliente"
        )
    
    return crud.actualizar_cliente(db, cliente_id, cliente)

@app.delete(
    "/clientes/{cliente_id}",
    tags=["Clientes"],
    summary="Eliminar cliente",
    response_model=schemas.Cliente
)
def eliminar_cliente(
    cliente_id: int, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Eliminar cliente. Solo accesible para administradores."""
    db_cliente = crud.eliminar_cliente(db, cliente_id)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return db_cliente

@app.put(
    "/categorias/{categoria_id}",
    tags=["Categorías"],
    summary="Actualizar categoría",
    response_model=schemas.Categoria
)
def actualizar_categoria(
    categoria_id: int, 
    categoria: schemas.CategoriaCreate, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Actualizar categoría. Solo accesible para administradores."""
    db_categoria = crud.actualizar_categoria(db, categoria_id, categoria)
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return db_categoria

@app.delete(
    "/categorias/{categoria_id}",
    tags=["Categorías"],
    summary="Eliminar categoría",
    response_model=schemas.Categoria
)
def eliminar_categoria(
    categoria_id: int, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Eliminar categoría. Solo accesible para administradores."""
    db_categoria = crud.eliminar_categoria(db, categoria_id)
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return db_categoria

@app.put(
    "/productos/{producto_id}",
    tags=["Productos"],
    summary="Actualizar producto",
    response_model=schemas.Producto
)
def actualizar_producto(
    producto_id: int, 
    producto: schemas.ProductoCreate, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Actualizar producto. Solo accesible para administradores."""
    db_producto = crud.actualizar_producto(db, producto_id, producto)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return db_producto

@app.delete(
    "/productos/{id}",
    tags=["Productos"],
    summary="Eliminar producto"
)
def eliminar_producto(
    id: int, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Eliminar producto. Solo accesible para administradores."""
    db_producto = crud.eliminar_producto(db, id)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"mensaje": "Producto eliminado correctamente"}

@app.get(
    "/pedidos/{pedido_id}",
    tags=["Pedidos"],
    summary="Obtener pedido por ID",
    response_model=schemas.Pedido,
    responses={
        200: {"description": "Pedido encontrado"},
        404: {"description": "Pedido no encontrado"},
        403: {"description": "Solo puedes ver tus propios pedidos"},
        401: {"description": "No autenticado"}
    }
)
def obtener_pedido(
    pedido_id: int = Path(..., description="ID del pedido"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene un pedido específico por ID.
    
    - Los clientes solo pueden ver sus propios pedidos.
    - Los administradores pueden ver cualquier pedido.
    """
    db_pedido = crud.get_pedido(db, pedido_id)
    if not db_pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar propiedad del recurso
    if user_role not in ["admin", "super_admin"]:
        cliente = crud.get_cliente(db, db_pedido.id_cliente)
        if not cliente or cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes ver tus propios pedidos"
            )
    
    return db_pedido

@app.put(
    "/pedidos/{pedido_id}",
    tags=["Pedidos"],
    summary="Actualizar pedido",
    response_model=schemas.Pedido
)
def actualizar_pedido(
    pedido_id: int, 
    pedido: schemas.PedidoCreate, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar pedido. Los clientes solo pueden actualizar sus propios pedidos.
    Los administradores pueden actualizar cualquier pedido.
    """
    db_pedido = crud.get_pedido(db, pedido_id)
    if not db_pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar propiedad del recurso
    if user_role not in ["admin", "super_admin"]:
        cliente = crud.get_cliente(db, db_pedido.id_cliente)
        if not cliente or cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes actualizar tus propios pedidos"
            )
    
    return crud.actualizar_pedido(db, pedido_id, pedido)

@app.delete(
    "/pedidos/{pedido_id}",
    tags=["Pedidos"],
    summary="Eliminar pedido",
    response_model=schemas.Pedido
)
def eliminar_pedido(
    pedido_id: int, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Eliminar pedido. Solo accesible para administradores."""
    db_pedido = crud.eliminar_pedido(db, pedido_id)
    if not db_pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return db_pedido

@app.put(
    "/detalle_pedidos/{detalle_id}",
    tags=["Pedidos"],
    summary="Actualizar detalle de pedido",
    response_model=schemas.DetallePedido
)
def actualizar_detalle_pedido(
    detalle_id: int, 
    detalle: schemas.DetallePedidoCreate, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar detalle de pedido. Los clientes solo pueden actualizar detalles de sus propios pedidos.
    Los administradores pueden actualizar cualquier detalle.
    """
    db_detalle = crud.get_detalle_pedido(db, detalle_id)
    if not db_detalle:
        raise HTTPException(status_code=404, detail="Detalle de pedido no encontrado")
    
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar propiedad del recurso
    if user_role not in ["admin", "super_admin"]:
        pedido = crud.get_pedido(db, db_detalle.id_pedido)
        if pedido:
            cliente = crud.get_cliente(db, pedido.id_cliente)
            if not cliente or cliente.id_usuario != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Solo puedes actualizar detalles de tus propios pedidos"
                )
    
    return crud.actualizar_detalle_pedido(db, detalle_id, detalle)

@app.delete(
    "/detalle_pedidos/{detalle_id}",
    tags=["Pedidos"],
    summary="Eliminar detalle de pedido",
    response_model=schemas.DetallePedido
)
def eliminar_detalle_pedido(
    detalle_id: int, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Eliminar detalle de pedido. Los clientes solo pueden eliminar detalles de sus propios pedidos.
    Los administradores pueden eliminar cualquier detalle.
    """
    db_detalle = crud.get_detalle_pedido(db, detalle_id)
    if not db_detalle:
        raise HTTPException(status_code=404, detail="Detalle de pedido no encontrado")
    
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar propiedad del recurso
    if user_role not in ["admin", "super_admin"]:
        pedido = crud.get_pedido(db, db_detalle.id_pedido)
        if pedido:
            cliente = crud.get_cliente(db, pedido.id_cliente)
            if not cliente or cliente.id_usuario != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Solo puedes eliminar detalles de tus propios pedidos"
                )
    
    return crud.eliminar_detalle_pedido(db, detalle_id)

@app.get(
    "/pedidos/{pedido_id}/productos",
    tags=["Pedidos"],
    summary="Obtener productos de un pedido",
    response_model=list[schemas.Producto]
)
def productos_de_pedido(
    pedido_id: int, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene los productos de un pedido específico.
    Los clientes solo pueden ver productos de sus propios pedidos.
    Los administradores pueden ver productos de cualquier pedido.
    Optimizado para evitar queries N+1 usando joinedload.
    """
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar propiedad del recurso si es cliente
    if user_role not in ["admin", "super_admin"]:
        pedido = crud.get_pedido(db, pedido_id)
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        cliente = crud.get_cliente(db, pedido.id_cliente)
        if not cliente or cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes ver productos de tus propios pedidos"
            )
    
    from sqlalchemy.orm import joinedload
    detalles = db.query(models.DetallePedido)\
        .options(joinedload(models.DetallePedido.producto))\
        .filter(models.DetallePedido.id_pedido == pedido_id).all()
    productos = [d.producto for d in detalles if d.producto]
    return productos

@app.get(
    "/categorias/{categoria_id}/productos",
    tags=["Productos"],
    summary="Obtener productos por categoría",
    response_model=list[schemas.Producto],
    description="Endpoint público. No requiere autenticación.",
    responses={
        200: {"description": "Lista de productos de la categoría"},
        404: {"description": "Categoría no encontrada"}
    }
)
def productos_de_categoria(
    categoria_id: int = Path(..., description="ID de la categoría"),
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los productos de una categoría específica.
    
    Este endpoint es **público** y no requiere autenticación.
    """
    return db.query(models.Producto).filter(models.Producto.id_categoria == categoria_id).all()

@app.get(
    "/clientes/{cliente_id}/pedidos",
    tags=["Pedidos"],
    summary="Obtener pedidos de un cliente",
    response_model=list[schemas.Pedido]
)
def pedidos_de_cliente(
    cliente_id: int, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener pedidos de un cliente.
    Los clientes solo pueden ver sus propios pedidos.
    Los administradores pueden ver pedidos de cualquier cliente.
    """
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar propiedad del recurso si es cliente
    if user_role not in ["admin", "super_admin"]:
        cliente = crud.get_cliente(db, cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        if cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes ver tus propios pedidos"
            )
    
    return db.query(models.Pedido).filter(models.Pedido.id_cliente == cliente_id).all()

@app.get(
    "/pedidos/estado/{estado}",
    tags=["Pedidos"],
    summary="Listar pedidos por estado",
    response_model=list[schemas.Pedido]
)
def listar_pedidos_por_estado(
    estado: str, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar pedidos por estado.
    Los clientes solo pueden ver sus propios pedidos filtrados por estado.
    Los administradores pueden ver todos los pedidos filtrados por estado.
    """
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    if user_role in ["admin", "super_admin"]:
        return db.query(models.Pedido).filter(models.Pedido.estado == estado).all()
    else:
        # Cliente solo ve sus propios pedidos
        cliente = crud.get_cliente_por_id_usuario(db, user_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        return db.query(models.Pedido)\
            .filter(models.Pedido.id_cliente == cliente.id_cliente)\
            .filter(models.Pedido.estado == estado).all()

@app.post(
    "/carritos/",
    tags=["Carritos"],
    summary="Crear carrito",
    response_model=schemas.Carrito,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Carrito creado exitosamente"},
        403: {"description": "Solo puedes crear carritos para tu propia cuenta"},
        401: {"description": "No autenticado"}
    }
)
def crear_carrito(
    carrito: schemas.CarritoCreate, 
    current_user: dict = Depends(require_cliente_or_admin()),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo carrito de compra.
    
    - Los clientes solo pueden crear carritos para sí mismos.
    - Los administradores pueden crear carritos para cualquier cliente.
    """
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar que el cliente solo pueda crear carritos para sí mismo
    if user_role not in ["admin", "super_admin"]:
        cliente = crud.get_cliente(db, carrito.id_cliente)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        if cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes crear carritos para tu propia cuenta"
            )
    
    return crud.crear_carrito(db=db, carrito=carrito)

@app.get(
    "/carritos/",
    tags=["Carritos"],
    summary="Listar carritos",
    response_model=list[schemas.Carrito]
)
def listar_carritos(
    skip: int = 0, 
    limit: int = 100, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Listar todos los carritos. Solo accesible para administradores."""
    return crud.get_carritos(db, skip=skip, limit=limit)

@app.put(
    "/carritos/{carrito_id}",
    tags=["Carritos"],
    summary="Actualizar carrito",
    response_model=schemas.Carrito
)
def actualizar_carrito(
    carrito_id: int, 
    carrito: schemas.CarritoCreate, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar carrito. Los clientes solo pueden actualizar sus propios carritos.
    Los administradores pueden actualizar cualquier carrito.
    """
    db_carrito = crud.get_carrito(db, carrito_id)
    if not db_carrito:
        raise HTTPException(status_code=404, detail="Carrito no encontrado")
    
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar propiedad del recurso
    if user_role not in ["admin", "super_admin"]:
        cliente = crud.get_cliente(db, db_carrito.id_cliente)
        if not cliente or cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes actualizar tus propios carritos"
            )
    
    return crud.actualizar_carrito(db, carrito_id, carrito)

@app.delete(
    "/carritos/{carrito_id}",
    tags=["Carritos"],
    summary="Eliminar carrito",
    response_model=schemas.Carrito
)
def eliminar_carrito(
    carrito_id: int, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Eliminar carrito. Los clientes solo pueden eliminar sus propios carritos.
    Los administradores pueden eliminar cualquier carrito.
    """
    db_carrito = crud.get_carrito(db, carrito_id)
    if not db_carrito:
        raise HTTPException(status_code=404, detail="Carrito no encontrado")
    
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar propiedad del recurso
    if user_role not in ["admin", "super_admin"]:
        cliente = crud.get_cliente(db, db_carrito.id_cliente)
        if not cliente or cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes eliminar tus propios carritos"
            )
    
    return crud.eliminar_carrito(db, carrito_id)

@app.post(
    "/detalle_carrito/",
    tags=["Carritos"],
    summary="Crear detalle de carrito",
    response_model=schemas.DetalleCarrito,
    status_code=status.HTTP_201_CREATED
)
def crear_detalle_carrito(
    detalle: schemas.DetalleCarritoCreate, 
    current_user: dict = Depends(require_cliente_or_admin()),
    db: Session = Depends(get_db)
):
    """
    Crear detalle de carrito. Los clientes solo pueden agregar detalles a sus propios carritos.
    Los administradores pueden agregar detalles a cualquier carrito.
    """
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar que el carrito pertenezca al usuario si es cliente
    if user_role not in ["admin", "super_admin"]:
        carrito = crud.get_carrito(db, detalle.id_carrito)
        if not carrito:
            raise HTTPException(status_code=404, detail="Carrito no encontrado")
        
        cliente = crud.get_cliente(db, carrito.id_cliente)
        if not cliente or cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes agregar productos a tus propios carritos"
            )
    
    return crud.crear_detalle_carrito(db=db, detalle=detalle)

@app.get(
    "/detalle_carrito/",
    tags=["Carritos"],
    summary="Listar detalles de carrito",
    response_model=list[schemas.DetalleCarrito]
)
def listar_detalles_carrito(
    skip: int = 0, 
    limit: int = 100, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Listar todos los detalles de carrito. Solo accesible para administradores."""
    return crud.get_detalles_carrito(db, skip=skip, limit=limit)

@app.put(
    "/detalle_carrito/{detalle_id}",
    tags=["Carritos"],
    summary="Actualizar detalle de carrito",
    response_model=schemas.DetalleCarrito
)
def actualizar_detalle_carrito(
    detalle_id: int, 
    detalle: schemas.DetalleCarritoCreate, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar detalle de carrito. Los clientes solo pueden actualizar detalles de sus propios carritos.
    Los administradores pueden actualizar cualquier detalle.
    """
    db_detalle = crud.get_detalle_carrito(db, detalle_id)
    if not db_detalle:
        raise HTTPException(status_code=404, detail="Detalle de carrito no encontrado")
    
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar propiedad del recurso
    if user_role not in ["admin", "super_admin"]:
        carrito = crud.get_carrito(db, db_detalle.id_carrito)
        if carrito:
            cliente = crud.get_cliente(db, carrito.id_cliente)
            if not cliente or cliente.id_usuario != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Solo puedes actualizar detalles de tus propios carritos"
                )
    
    return crud.actualizar_detalle_carrito(db, detalle_id, detalle)

@app.delete(
    "/detalle_carrito/{detalle_id}",
    tags=["Carritos"],
    summary="Eliminar detalle de carrito"
)
def eliminar_detalle_carrito(
    detalle_id: int, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Eliminar detalle de carrito. Los clientes solo pueden eliminar detalles de sus propios carritos.
    Los administradores pueden eliminar cualquier detalle.
    """
    db_detalle = crud.get_detalle_carrito(db, detalle_id)
    if not db_detalle:
        raise HTTPException(status_code=404, detail="Detalle de carrito no encontrado")
    
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar propiedad del recurso
    if user_role not in ["admin", "super_admin"]:
        carrito = crud.get_carrito(db, db_detalle.id_carrito)
        if carrito:
            cliente = crud.get_cliente(db, carrito.id_cliente)
            if not cliente or cliente.id_usuario != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Solo puedes eliminar detalles de tus propios carritos"
                )
    
    return crud.eliminar_detalle_carrito(db, detalle_id)

@app.get(
    "/clientes/{cliente_id}/carritos",
    tags=["Carritos"],
    summary="Obtener carritos de un cliente",
    response_model=list[schemas.Carrito]
)
def carritos_de_cliente(
    cliente_id: int, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener carritos de un cliente.
    Los clientes solo pueden ver sus propios carritos.
    Los administradores pueden ver carritos de cualquier cliente.
    """
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar propiedad del recurso si es cliente
    if user_role not in ["admin", "super_admin"]:
        cliente = crud.get_cliente(db, cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        if cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes ver tus propios carritos"
            )
    
    return db.query(models.Carrito).filter(models.Carrito.id_cliente == cliente_id).all()

@app.get(
    "/carritos/{carrito_id}/productos",
    tags=["Carritos"],
    summary="Obtener productos de un carrito",
    response_model=list[schemas.Producto]
)
def productos_de_carrito(
    carrito_id: int, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene los productos de un carrito específico.
    Los clientes solo pueden ver productos de sus propios carritos.
    Los administradores pueden ver productos de cualquier carrito.
    Optimizado para evitar queries N+1 usando joinedload.
    """
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar propiedad del recurso si es cliente
    if user_role not in ["admin", "super_admin"]:
        carrito = crud.get_carrito(db, carrito_id)
        if not carrito:
            raise HTTPException(status_code=404, detail="Carrito no encontrado")
        
        cliente = crud.get_cliente(db, carrito.id_cliente)
        if not cliente or cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes ver productos de tus propios carritos"
            )
    
    from sqlalchemy.orm import joinedload
    detalles = db.query(models.DetalleCarrito)\
        .options(joinedload(models.DetalleCarrito.producto))\
        .filter(models.DetalleCarrito.id_carrito == carrito_id).all()
    productos = [d.producto for d in detalles if d.producto]
    return productos

@app.post(
    "/login",
    tags=["Autenticación"],
    summary="Iniciar sesión",
    response_description="Token JWT de acceso",
    responses={
        200: {
            "description": "Login exitoso",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {
            "description": "Credenciales incorrectas",
            "content": {
                "application/json": {
                    "example": {"detail": "Credenciales incorrectas"}
                }
            }
        },
        403: {
            "description": "Cuenta no confirmada",
            "content": {
                "application/json": {
                    "example": {"detail": "Debes confirmar tu cuenta antes de iniciar sesión. Revisa tu correo para obtener el PIN de confirmación o solicita uno nuevo."}
                }
            }
        },
        422: {
            "description": "Error de validación",
            "content": {
                "application/json": {
                    "example": {"detail": "Se requieren correo y contraseña"}
                }
            }
        }
    }
)
def login(datos: dict = Body(..., example={"correo": "usuario@ejemplo.com", "contraseña": "miPassword123"}), db: Session = Depends(get_db)):
    """
    Inicia sesión con correo y contraseña.
    
    Retorna un token JWT que debe ser usado en el header `Authorization: Bearer <token>`
    para acceder a los endpoints protegidos.
    
    **El token expira en 60 minutos por defecto.**
    
    **Importante**: La cuenta debe estar confirmada antes de poder iniciar sesión.
    Si no has confirmado tu cuenta, recibirás un error 403. Puedes solicitar un nuevo
    PIN de confirmación usando `/usuarios/reenviar-confirmacion`.
    
    El token incluye:
    - `sub`: Correo del usuario
    - `id_usuario`: ID del usuario
    - `rol`: Rol del usuario (cliente, admin o super_admin)
    """
    correo = datos.get("correo")
    contraseña = datos.get("contraseña")
    
    # Validar que se proporcionaron ambos campos
    if not correo or not contraseña:
        raise HTTPException(status_code=422, detail="Se requieren correo y contraseña")
    
    usuario = crud.get_usuario_por_correo(db, correo=correo)
    if not usuario or not verify_password(contraseña, usuario.contraseña):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    # Validar que la cuenta esté confirmada
    if usuario.email_verificado != "S":
        raise HTTPException(
            status_code=403,
            detail="Debes confirmar tu cuenta antes de iniciar sesión. Revisa tu correo para obtener el PIN de confirmación o solicita uno nuevo."
        )
    
    # Crear el token
    token = crear_token_de_acceso({"sub": usuario.correo, "id_usuario": usuario.id_usuario, "rol": usuario.rol})
    return {
        "access_token": token,
        "token_type": "bearer"
    }

@app.get(
    "/usuarios/me",
    tags=["Usuarios"],
    summary="Obtener usuario actual",
    response_description="Información del usuario autenticado",
    responses={
        200: {"description": "Información del usuario"},
        401: {"description": "No autenticado"}
    }
)
def leer_usuarios_me(current_user: dict = Depends(get_current_user)):
    """
    Obtiene la información del usuario autenticado actual.
    
    Requiere autenticación mediante token JWT.
    """
    return current_user

# ============================================
# ENDPOINTS DE CONFIRMACIÓN Y RECUPERACIÓN
# ============================================

@app.post(
    "/usuarios/confirmar-cuenta",
    tags=["Autenticación"],
    summary="Confirmar cuenta con PIN",
    response_model=schemas.ConfirmarCuentaResponse,
    responses={
        200: {"description": "Cuenta confirmada exitosamente"},
        400: {"description": "PIN inválido o expirado"},
        404: {"description": "Usuario no encontrado"}
    }
)
def confirmar_cuenta(
    request: schemas.ConfirmarCuentaRequest,
    db: Session = Depends(get_db)
):
    """
    Confirma la cuenta de un usuario usando el correo y PIN recibido por email.
    
    Este endpoint debe ser llamado después del registro para activar la cuenta.
    El usuario debe ingresar el PIN de 6 dígitos que recibió en su correo electrónico.
    
    **Flujo**:
    1. Usuario se registra en `/usuarios/`
    2. Recibe un PIN de 6 dígitos por email
    3. Ingresa el PIN en la misma página de registro
    4. Frontend llama a este endpoint con correo + PIN
    5. Cuenta confirmada, usuario puede hacer login
    """
    usuario = crud.confirmar_cuenta(db, request.correo, request.pin)
    return schemas.ConfirmarCuentaResponse(
        mensaje="Cuenta confirmada exitosamente",
        email_verificado=True
    )


@app.post(
    "/usuarios/reenviar-confirmacion",
    tags=["Autenticación"],
    summary="Reenviar PIN de confirmación",
    response_model=schemas.ReenviarConfirmacionResponse
)
def reenviar_confirmacion(
    request: schemas.ReenviarConfirmacionRequest,
    db: Session = Depends(get_db)
):
    """
    Reenvía el email de confirmación con un nuevo PIN.
    
    Útil si no recibiste el email inicial o el PIN expiró.
    El nuevo PIN expirará en 15 minutos.
    """
    nuevo_pin = crud.regenerar_token_confirmacion(db, request.correo)
    
    # Enviar email
    from . import email_service
    usuario = crud.get_usuario_por_correo(db, request.correo)
    nombre = request.correo.split("@")[0]
    cliente = crud.get_cliente_por_id_usuario(db, usuario.id_usuario)
    if cliente:
        nombre = f"{cliente.nombre} {cliente.apellido}"
    
    email_service.enviar_email_confirmacion(
        destinatario=request.correo,
        nombre=nombre,
        pin=nuevo_pin
    )
    
    return schemas.ReenviarConfirmacionResponse(
        mensaje="PIN de confirmación reenviado. Revisa tu bandeja de entrada."
    )


@app.post(
    "/usuarios/solicitar-recuperacion",
    tags=["Autenticación"],
    summary="Solicitar recuperación de contraseña",
    response_model=schemas.SolicitarRecuperacionResponse
)
def solicitar_recuperacion(
    request: schemas.SolicitarRecuperacionRequest,
    db: Session = Depends(get_db)
):
    """
    Solicita un PIN de recuperación de contraseña.
    
    Se envía un PIN de 6 dígitos al correo del usuario.
    El PIN expira después de un tiempo determinado.
    """
    try:
        pin = crud.generar_pin_recuperacion(db, request.correo)
        
        # Enviar email con PIN
        from . import email_service
        usuario = crud.get_usuario_por_correo(db, request.correo)
        nombre = request.correo.split("@")[0]
        cliente = crud.get_cliente_por_id_usuario(db, usuario.id_usuario)
        if cliente:
            nombre = f"{cliente.nombre} {cliente.apellido}"
        
        email_service.enviar_email_recuperacion(
            destinatario=request.correo,
            nombre=nombre,
            pin=pin
        )
        
        return schemas.SolicitarRecuperacionResponse(
            mensaje="Se ha enviado un PIN de recuperación a tu correo. Revisa tu bandeja de entrada."
        )
    except HTTPException:
        # Por seguridad, siempre retornamos el mismo mensaje
        return schemas.SolicitarRecuperacionResponse(
            mensaje="Si el correo existe, se ha enviado un PIN de recuperación."
        )


@app.post(
    "/usuarios/validar-pin",
    tags=["Autenticación"],
    summary="Validar PIN de recuperación",
    response_model=schemas.ValidarPinResponse
)
def validar_pin(
    request: schemas.ValidarPinRequest,
    db: Session = Depends(get_db)
):
    """
    Valida un PIN de recuperación de contraseña.
    
    Útil para verificar el PIN antes de mostrar el formulario de cambio de contraseña.
    """
    es_valido = crud.validar_pin_recuperacion(db, request.correo, request.pin)
    
    if es_valido:
        return schemas.ValidarPinResponse(
            valido=True,
            mensaje="PIN válido. Puedes proceder a cambiar tu contraseña."
        )
    else:
        return schemas.ValidarPinResponse(
            valido=False,
            mensaje="PIN inválido o expirado. Solicita un nuevo PIN."
        )


@app.post(
    "/usuarios/cambiar-contraseña",
    tags=["Autenticación"],
    summary="Cambiar contraseña con PIN",
    response_model=schemas.CambiarContraseñaResponse
)
def cambiar_contraseña(
    request: schemas.CambiarContraseñaRequest,
    db: Session = Depends(get_db)
):
    """
    Cambia la contraseña usando PIN de recuperación.
    
    Requiere el PIN válido obtenido de `/usuarios/solicitar-recuperacion`.
    """
    crud.cambiar_contraseña_con_pin(
        db,
        request.correo,
        request.pin,
        request.nueva_contraseña
    )
    
    return schemas.CambiarContraseñaResponse(
        mensaje="Contraseña cambiada exitosamente. Ya puedes iniciar sesión con tu nueva contraseña."
    )


@app.post(
    "/usuarios/cambiar-contraseña-autenticado",
    tags=["Usuarios"],
    summary="Cambiar contraseña (autenticado)",
    response_model=schemas.CambiarContraseñaAutenticadoResponse,
    responses={
        200: {"description": "Contraseña cambiada exitosamente"},
        401: {"description": "No autenticado"},
        400: {"description": "Contraseña actual incorrecta"}
    }
)
def cambiar_contraseña_autenticado(
    request: schemas.CambiarContraseñaAutenticadoRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cambia la contraseña de un usuario autenticado.
    
    Requiere la contraseña actual para validar la identidad.
    Solo puedes cambiar tu propia contraseña.
    """
    usuario_id = current_user.get("id_usuario")
    crud.cambiar_contraseña_usuario(
        db,
        usuario_id,
        request.contraseña_actual,
        request.nueva_contraseña
    )
    
    return schemas.CambiarContraseñaAutenticadoResponse(
        mensaje="Contraseña cambiada exitosamente."
    )

# ============================================
# ENDPOINTS DE AUDITORÍA
# ============================================

@app.get(
    "/audit/",
    tags=["Auditoría"],
    summary="Listar logs de auditoría",
    response_model=list[schemas.AuditLog],
    responses={
        200: {"description": "Lista de logs de auditoría"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo administradores"}
    }
)
def listar_audit_logs(
    skip: int = Query(0, ge=0, description="Número de registros a saltar (paginación)"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros a retornar"),
    tabla_nombre: Optional[str] = Query(None, description="Filtrar por nombre de tabla"),
    registro_id: Optional[int] = Query(None, description="Filtrar por ID de registro específico"),
    accion: Optional[str] = Query(None, description="Filtrar por tipo de acción (INSERT, UPDATE, DELETE)"),
    usuario_id: Optional[int] = Query(None, description="Filtrar por usuario que realizó la acción"),
    fecha_desde: Optional[datetime] = Query(None, description="Filtrar desde una fecha específica"),
    fecha_hasta: Optional[datetime] = Query(None, description="Filtrar hasta una fecha específica"),
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Obtiene logs de auditoría con filtros opcionales.
    
    **Solo accesible para administradores.**
    
    Filtros disponibles:
    - **tabla_nombre**: Filtrar por nombre de tabla
    - **registro_id**: Filtrar por ID de registro específico
    - **accion**: Filtrar por tipo de acción (INSERT, UPDATE, DELETE)
    - **usuario_id**: Filtrar por usuario que realizó la acción
    - **fecha_desde**: Filtrar desde una fecha específica
    - **fecha_hasta**: Filtrar hasta una fecha específica
    """
    return crud.get_audit_logs(
        db=db,
        skip=skip,
        limit=limit,
        tabla_nombre=tabla_nombre,
        registro_id=registro_id,
        accion=accion,
        usuario_id=usuario_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )

@app.get(
    "/audit/{tabla_nombre}/{registro_id}",
    tags=["Auditoría"],
    summary="Obtener historial de un registro",
    response_model=list[schemas.AuditLog],
    responses={
        200: {"description": "Historial del registro"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo administradores"}
    }
)
def obtener_historial_registro(
    tabla_nombre: str = Path(..., description="Nombre de la tabla (ej: productos, usuarios)"),
    registro_id: int = Path(..., description="ID del registro"),
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial completo de cambios de un registro específico.
    
    **Solo accesible para administradores.**
    
    Ejemplos:
    - `GET /audit/productos/123` -> Historial completo del producto con ID 123
    - `GET /audit/usuarios/456` -> Historial completo del usuario con ID 456
    """
    return crud.get_audit_logs(
        db=db,
        tabla_nombre=tabla_nombre,
        registro_id=registro_id
    )
