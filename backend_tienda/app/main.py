"""
FastAPI application entry point.

- Defines the application, routes, and dependency injection for the backend API.
- Configures CORS and the database connection.
- Main dependencies: FastAPI, SQLAlchemy, local modules (models, schemas, crud, auth, database)
"""

import os
from fastapi import FastAPI, Depends, HTTPException, Body, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime
from . import models, schemas, crud
from .database import SessionLocal, engine
from .auth import crear_token_de_acceso, get_current_user, verify_password, require_admin, require_cliente_or_admin, verify_resource_owner, verificar_token
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

app = FastAPI()

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

@app.get("/")
def root():
    """Endpoint raíz para verificar que el servidor está funcionando."""
    return {
        "status": "ok",
        "message": "API funcionando correctamente",
        "service": "backend-tienda",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    """Endpoint de health check para monitoreo."""
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

@app.post("/usuarios/", response_model=schemas.Usuario)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    """Crear nuevo usuario y enviar email de confirmación."""
    db_usuario = crud.get_usuario_por_correo(db, correo=usuario.correo)
    if db_usuario:
        raise HTTPException(status_code=400, detail="Correo ya registrado")
    
    nuevo_usuario = crud.crear_usuario(db=db, usuario=usuario)
    
    # Enviar email de confirmación
    from . import email_service
    # Obtener nombre del usuario si tiene perfil de cliente
    nombre = usuario.correo.split("@")[0]  # Usar parte del email como nombre temporal
    cliente = crud.get_cliente_por_id_usuario(db, nuevo_usuario.id_usuario)
    if cliente:
        nombre = f"{cliente.nombre} {cliente.apellido}"
    
    email_service.enviar_email_confirmacion(
        destinatario=nuevo_usuario.correo,
        nombre=nombre,
        token=nuevo_usuario.token_confirmacion
    )
    
    return nuevo_usuario

@app.post("/clientes/", response_model=schemas.Cliente)
def crear_cliente(
    cliente: schemas.ClienteCreate, 
    current_user: dict = Depends(require_cliente_or_admin()),
    db: Session = Depends(get_db)
):
    """
    Crear cliente. Los clientes solo pueden crear su propio perfil.
    Los administradores pueden crear cualquier perfil.
    """
    # Validar que el cliente solo pueda crear su propio perfil
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    if user_role != "admin" and cliente.id_usuario != user_id:
        raise HTTPException(
            status_code=403, 
            detail="Solo puedes crear tu propio perfil de cliente"
        )
    
    return crud.crear_cliente(db=db, cliente=cliente)

@app.get("/clientes/", response_model=list[schemas.Cliente])
def listar_clientes(
    skip: int = 0, 
    limit: int = 100, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Listar todos los clientes. Solo accesible para administradores."""
    return crud.get_clientes(db, skip=skip, limit=limit)

@app.get("/clientes/usuario/{id_usuario}", response_model=schemas.Cliente)
def obtener_cliente_por_usuario(
    id_usuario: int, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener cliente por ID de usuario. 
    Los clientes solo pueden ver su propio perfil.
    Los administradores pueden ver cualquier perfil.
    """
    # Validar propiedad del recurso
    verify_resource_owner(id_usuario, current_user)
    
    cliente = crud.get_cliente_por_id_usuario(db, id_usuario)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@app.get("/clientes/{cliente_id}", response_model=schemas.Cliente)
def obtener_cliente(
    cliente_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener un cliente específico por ID.
    Los clientes solo pueden ver su propio perfil.
    Los administradores pueden ver cualquier perfil.
    """
    cliente = crud.get_cliente(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Validar propiedad del recurso
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    if user_role != "admin" and cliente.id_usuario != user_id:
        raise HTTPException(
            status_code=403,
            detail="Solo puedes ver tu propio perfil"
        )
    
    return cliente

@app.post("/categorias/", response_model=schemas.Categoria)
def crear_categoria(
    categoria: schemas.CategoriaCreate, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Crear categoría. Solo accesible para administradores."""
    return crud.crear_categoria(db=db, categoria=categoria)

@app.get("/categorias/", response_model=list[schemas.Categoria])
def listar_categorias(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_categorias(db, skip=skip, limit=limit)

@app.get("/categorias/{categoria_id}", response_model=schemas.Categoria)
def obtener_categoria(categoria_id: int, db: Session = Depends(get_db)):
    """Obtener una categoría específica por ID."""
    categoria = crud.get_categoria(db, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria

@app.post("/productos/", response_model=schemas.Producto)
def crear_producto(
    producto: schemas.ProductoCreate, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Crear producto. Solo accesible para administradores."""
    return crud.crear_producto(db=db, producto=producto)

@app.get("/productos/", response_model=list[schemas.Producto])
def listar_productos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_productos(db, skip=skip, limit=limit)

@app.get("/productos/{producto_id}", response_model=schemas.Producto)
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    """Obtener un producto específico por ID."""
    producto = crud.get_producto(db, producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@app.post("/pedidos/", response_model=schemas.Pedido)
def crear_pedido(
    pedido: schemas.PedidoCreate, 
    current_user: dict = Depends(require_cliente_or_admin()),
    db: Session = Depends(get_db)
):
    """
    Crear pedido. Los clientes solo pueden crear pedidos para sí mismos.
    Los administradores pueden crear pedidos para cualquier cliente.
    """
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar que el cliente solo pueda crear pedidos para sí mismo
    if user_role != "admin":
        cliente = crud.get_cliente(db, pedido.id_cliente)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        if cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes crear pedidos para tu propia cuenta"
            )
    
    return crud.crear_pedido(db=db, pedido=pedido)

@app.get("/pedidos/", response_model=list[schemas.Pedido])
def listar_pedidos(
    skip: int = 0, 
    limit: int = 100, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Listar todos los pedidos. Solo accesible para administradores."""
    return crud.get_pedidos(db, skip=skip, limit=limit)

@app.post("/detalle_pedidos/", response_model=schemas.DetallePedido)
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
    if user_role != "admin":
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

@app.get("/detalle_pedidos/", response_model=list[schemas.DetallePedido])
def listar_detalles_pedido(
    skip: int = 0, 
    limit: int = 100, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Listar todos los detalles de pedidos. Solo accesible para administradores."""
    return crud.get_detalles_pedido(db, skip=skip, limit=limit)

@app.put("/usuarios/{usuario_id}", response_model=schemas.Usuario)
def actualizar_usuario(
    usuario_id: int, 
    usuario: schemas.UsuarioCreate, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Actualizar usuario. Solo accesible para administradores."""
    db_usuario = crud.actualizar_usuario(db, usuario_id, usuario)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario

@app.delete("/usuarios/{usuario_id}", response_model=schemas.Usuario)
def eliminar_usuario(
    usuario_id: int, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Eliminar usuario. Solo accesible para administradores."""
    db_usuario = crud.eliminar_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario

@app.put("/clientes/{cliente_id}", response_model=schemas.Cliente)
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
    
    if user_role != "admin" and db_cliente.id_usuario != user_id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para actualizar este cliente"
        )
    
    return crud.actualizar_cliente(db, cliente_id, cliente)

@app.delete("/clientes/{cliente_id}", response_model=schemas.Cliente)
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

@app.put("/categorias/{categoria_id}", response_model=schemas.Categoria)
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

@app.delete("/categorias/{categoria_id}", response_model=schemas.Categoria)
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

@app.put("/productos/{producto_id}", response_model=schemas.Producto)
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

@app.delete("/productos/{id}")
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

@app.get("/pedidos/{pedido_id}", response_model=schemas.Pedido)
def obtener_pedido(
    pedido_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener un pedido específico por ID.
    Los clientes solo pueden ver sus propios pedidos.
    Los administradores pueden ver cualquier pedido.
    """
    db_pedido = crud.get_pedido(db, pedido_id)
    if not db_pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar propiedad del recurso
    if user_role != "admin":
        cliente = crud.get_cliente(db, db_pedido.id_cliente)
        if not cliente or cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes ver tus propios pedidos"
            )
    
    return db_pedido

@app.put("/pedidos/{pedido_id}", response_model=schemas.Pedido)
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
    if user_role != "admin":
        cliente = crud.get_cliente(db, db_pedido.id_cliente)
        if not cliente or cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes actualizar tus propios pedidos"
            )
    
    return crud.actualizar_pedido(db, pedido_id, pedido)

@app.delete("/pedidos/{pedido_id}", response_model=schemas.Pedido)
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

@app.put("/detalle_pedidos/{detalle_id}", response_model=schemas.DetallePedido)
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
    if user_role != "admin":
        pedido = crud.get_pedido(db, db_detalle.id_pedido)
        if pedido:
            cliente = crud.get_cliente(db, pedido.id_cliente)
            if not cliente or cliente.id_usuario != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Solo puedes actualizar detalles de tus propios pedidos"
                )
    
    return crud.actualizar_detalle_pedido(db, detalle_id, detalle)

@app.delete("/detalle_pedidos/{detalle_id}", response_model=schemas.DetallePedido)
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
    if user_role != "admin":
        pedido = crud.get_pedido(db, db_detalle.id_pedido)
        if pedido:
            cliente = crud.get_cliente(db, pedido.id_cliente)
            if not cliente or cliente.id_usuario != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Solo puedes eliminar detalles de tus propios pedidos"
                )
    
    return crud.eliminar_detalle_pedido(db, detalle_id)

@app.get("/pedidos/{pedido_id}/productos", response_model=list[schemas.Producto])
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
    if user_role != "admin":
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

@app.get("/categorias/{categoria_id}/productos", response_model=list[schemas.Producto])
def productos_de_categoria(categoria_id: int, db: Session = Depends(get_db)):
    return db.query(models.Producto).filter(models.Producto.id_categoria == categoria_id).all()

@app.get("/clientes/{cliente_id}/pedidos", response_model=list[schemas.Pedido])
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
    if user_role != "admin":
        cliente = crud.get_cliente(db, cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        if cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes ver tus propios pedidos"
            )
    
    return db.query(models.Pedido).filter(models.Pedido.id_cliente == cliente_id).all()

@app.get("/pedidos/estado/{estado}", response_model=list[schemas.Pedido])
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
    
    if user_role == "admin":
        return db.query(models.Pedido).filter(models.Pedido.estado == estado).all()
    else:
        # Cliente solo ve sus propios pedidos
        cliente = crud.get_cliente_por_id_usuario(db, user_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        return db.query(models.Pedido)\
            .filter(models.Pedido.id_cliente == cliente.id_cliente)\
            .filter(models.Pedido.estado == estado).all()

@app.post("/carritos/", response_model=schemas.Carrito)
def crear_carrito(
    carrito: schemas.CarritoCreate, 
    current_user: dict = Depends(require_cliente_or_admin()),
    db: Session = Depends(get_db)
):
    """
    Crear carrito. Los clientes solo pueden crear carritos para sí mismos.
    Los administradores pueden crear carritos para cualquier cliente.
    """
    user_id = current_user.get("id_usuario")
    user_role = current_user.get("rol")
    
    # Validar que el cliente solo pueda crear carritos para sí mismo
    if user_role != "admin":
        cliente = crud.get_cliente(db, carrito.id_cliente)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        if cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes crear carritos para tu propia cuenta"
            )
    
    return crud.crear_carrito(db=db, carrito=carrito)

@app.get("/carritos/", response_model=list[schemas.Carrito])
def listar_carritos(
    skip: int = 0, 
    limit: int = 100, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Listar todos los carritos. Solo accesible para administradores."""
    return crud.get_carritos(db, skip=skip, limit=limit)

@app.put("/carritos/{carrito_id}", response_model=schemas.Carrito)
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
    if user_role != "admin":
        cliente = crud.get_cliente(db, db_carrito.id_cliente)
        if not cliente or cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes actualizar tus propios carritos"
            )
    
    return crud.actualizar_carrito(db, carrito_id, carrito)

@app.delete("/carritos/{carrito_id}", response_model=schemas.Carrito)
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
    if user_role != "admin":
        cliente = crud.get_cliente(db, db_carrito.id_cliente)
        if not cliente or cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes eliminar tus propios carritos"
            )
    
    return crud.eliminar_carrito(db, carrito_id)

@app.post("/detalle_carrito/", response_model=schemas.DetalleCarrito)
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
    if user_role != "admin":
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

@app.get("/detalle_carrito/", response_model=list[schemas.DetalleCarrito])
def listar_detalles_carrito(
    skip: int = 0, 
    limit: int = 100, 
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Listar todos los detalles de carrito. Solo accesible para administradores."""
    return crud.get_detalles_carrito(db, skip=skip, limit=limit)

@app.put("/detalle_carrito/{detalle_id}", response_model=schemas.DetalleCarrito)
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
    if user_role != "admin":
        carrito = crud.get_carrito(db, db_detalle.id_carrito)
        if carrito:
            cliente = crud.get_cliente(db, carrito.id_cliente)
            if not cliente or cliente.id_usuario != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Solo puedes actualizar detalles de tus propios carritos"
                )
    
    return crud.actualizar_detalle_carrito(db, detalle_id, detalle)

@app.delete("/detalle_carrito/{detalle_id}")
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
    if user_role != "admin":
        carrito = crud.get_carrito(db, db_detalle.id_carrito)
        if carrito:
            cliente = crud.get_cliente(db, carrito.id_cliente)
            if not cliente or cliente.id_usuario != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Solo puedes eliminar detalles de tus propios carritos"
                )
    
    return crud.eliminar_detalle_carrito(db, detalle_id)

@app.get("/clientes/{cliente_id}/carritos", response_model=list[schemas.Carrito])
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
    if user_role != "admin":
        cliente = crud.get_cliente(db, cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        if cliente.id_usuario != user_id:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes ver tus propios carritos"
            )
    
    return db.query(models.Carrito).filter(models.Carrito.id_cliente == cliente_id).all()

@app.get("/carritos/{carrito_id}/productos", response_model=list[schemas.Producto])
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
    if user_role != "admin":
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

@app.post("/login")
def login(datos: dict = Body(...), db: Session = Depends(get_db)):
    """
    Endpoint de login. Valida credenciales y retorna token JWT.
    """
    correo = datos.get("correo")
    contraseña = datos.get("contraseña")
    
    # Validar que se proporcionaron ambos campos
    if not correo or not contraseña:
        raise HTTPException(status_code=422, detail="Se requieren correo y contraseña")
    
    usuario = crud.get_usuario_por_correo(db, correo=correo)
    if not usuario or not verify_password(contraseña, usuario.contraseña):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    # Crear el token
    token = crear_token_de_acceso({"sub": usuario.correo, "id_usuario": usuario.id_usuario, "rol": usuario.rol})
    return {
        "access_token": token,
        "token_type": "bearer"
    }

@app.get("/usuarios/me")
def leer_usuarios_me(current_user: dict = Depends(get_current_user)):
    return current_user

# ============================================
# ENDPOINTS DE CONFIRMACIÓN Y RECUPERACIÓN
# ============================================

@app.post("/usuarios/confirmar-cuenta", response_model=schemas.ConfirmarCuentaResponse)
def confirmar_cuenta(
    request: schemas.ConfirmarCuentaRequest,
    db: Session = Depends(get_db)
):
    """
    Confirma la cuenta de un usuario usando el token recibido por email.
    """
    usuario = crud.confirmar_cuenta(db, request.token)
    return schemas.ConfirmarCuentaResponse(
        mensaje="Cuenta confirmada exitosamente",
        email_verificado=True
    )


@app.post("/usuarios/reenviar-confirmacion", response_model=schemas.ReenviarConfirmacionResponse)
def reenviar_confirmacion(
    request: schemas.ReenviarConfirmacionRequest,
    db: Session = Depends(get_db)
):
    """
    Reenvía el email de confirmación de cuenta.
    """
    nuevo_token = crud.regenerar_token_confirmacion(db, request.correo)
    
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
        token=nuevo_token
    )
    
    return schemas.ReenviarConfirmacionResponse(
        mensaje="Email de confirmación reenviado. Revisa tu bandeja de entrada."
    )


@app.post("/usuarios/solicitar-recuperacion", response_model=schemas.SolicitarRecuperacionResponse)
def solicitar_recuperacion(
    request: schemas.SolicitarRecuperacionRequest,
    db: Session = Depends(get_db)
):
    """
    Solicita un PIN de recuperación de contraseña.
    Se envía un PIN de 6 dígitos al correo del usuario.
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


@app.post("/usuarios/validar-pin", response_model=schemas.ValidarPinResponse)
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


@app.post("/usuarios/cambiar-contraseña", response_model=schemas.CambiarContraseñaResponse)
def cambiar_contraseña(
    request: schemas.CambiarContraseñaRequest,
    db: Session = Depends(get_db)
):
    """
    Cambia la contraseña usando PIN de recuperación.
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


@app.post("/usuarios/cambiar-contraseña-autenticado", response_model=schemas.CambiarContraseñaAutenticadoResponse)
def cambiar_contraseña_autenticado(
    request: schemas.CambiarContraseñaAutenticadoRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cambia la contraseña de un usuario autenticado.
    Requiere la contraseña actual para validar.
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

@app.get("/audit/", response_model=list[schemas.AuditLog])
def listar_audit_logs(
    skip: int = 0,
    limit: int = 100,
    tabla_nombre: Optional[str] = None,
    registro_id: Optional[int] = None,
    accion: Optional[str] = None,
    usuario_id: Optional[int] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Obtener logs de auditoría con filtros opcionales.
    Solo accesible para administradores.
    
    Filtros disponibles:
    - tabla_nombre: Filtrar por nombre de tabla
    - registro_id: Filtrar por ID de registro específico
    - accion: Filtrar por tipo de acción (INSERT, UPDATE, DELETE)
    - usuario_id: Filtrar por usuario que realizó la acción
    - fecha_desde: Filtrar desde una fecha específica
    - fecha_hasta: Filtrar hasta una fecha específica
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

@app.get("/audit/{tabla_nombre}/{registro_id}", response_model=list[schemas.AuditLog])
def obtener_historial_registro(
    tabla_nombre: str,
    registro_id: int,
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Obtener historial completo de cambios de un registro específico.
    Solo accesible para administradores.
    
    Ejemplo:
    - GET /audit/productos/123 -> Historial completo del producto con ID 123
    - GET /audit/usuarios/456 -> Historial completo del usuario con ID 456
    """
    return crud.get_audit_logs(
        db=db,
        tabla_nombre=tabla_nombre,
        registro_id=registro_id
    )
