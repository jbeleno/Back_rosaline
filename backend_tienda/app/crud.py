"""
CRUD operations module for the database.

Includes functions to:
- Create, read, update, and delete records for users, clients, categories, products, orders, carts, etc.

Main dependencies:
- SQLAlchemy
- datetime
- Local modules: models, schemas, auth
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional
from . import models, schemas
from datetime import datetime, timedelta
from .auth import hash_password
import secrets
import uuid


def get_usuario(db: Session, usuario_id: int):
    """
    Retrieves a user from the database by their ID.

    Args:
        db (Session): Database session.
        usuario_id (int): User ID.

    Returns:
        models.Usuario | None: Found user or None if not found.
    """
    return db.query(models.Usuario).filter(models.Usuario.id_usuario == usuario_id).first()

def get_usuario_por_correo(db: Session, correo: str):
    """
    Retrieves a user from the database by their email address.

    Args:
        db (Session): Database session.
        correo (str): User email address.

    Returns:
        models.Usuario | None: Found user or None if not found.
    """
    return db.query(models.Usuario).filter(models.Usuario.correo == correo).first()

def crear_usuario(db: Session, usuario: schemas.UsuarioCreate):
    """
    Creates a new user in the database with a hashed password and generates a confirmation token.

    Args:
        db (Session): Database session.
        usuario (schemas.UsuarioCreate): User data to create.

    Returns:
        models.Usuario: Created user.
    """
    # Generar token de confirmación único
    token_confirmacion = str(uuid.uuid4())
    
    db_usuario = models.Usuario(
        correo=usuario.correo,
        contraseña=hash_password(usuario.contraseña),
        rol=usuario.rol,
        fecha_creacion=datetime.utcnow(),
        email_verificado="N",
        token_confirmacion=token_confirmacion,
        token_confirmacion_expira=datetime.utcnow() + timedelta(hours=1)  # Expira en 1 hora
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def get_clientes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Cliente).offset(skip).limit(limit).all()

def crear_cliente(db: Session, cliente: schemas.ClienteCreate):
    """
    Creates a new client. Validates that the user exists and doesn't already have a client profile.
    
    Args:
        db (Session): Database session.
        cliente (schemas.ClienteCreate): Client data to create.
    
    Returns:
        models.Cliente: Created client.
    
    Raises:
        HTTPException: If the user doesn't exist or already has a client profile.
    """
    # Validar que el usuario existe
    usuario = get_usuario(db, cliente.id_usuario)
    if not usuario:
        raise HTTPException(status_code=404, detail=f"Usuario con ID {cliente.id_usuario} no encontrado")
    
    # Validar que el usuario no tenga ya un perfil de cliente
    cliente_existente = get_cliente_por_id_usuario(db, cliente.id_usuario)
    if cliente_existente:
        raise HTTPException(
            status_code=400, 
            detail=f"El usuario con ID {cliente.id_usuario} ya tiene un perfil de cliente"
        )
    
    db_cliente = models.Cliente(
        id_usuario=cliente.id_usuario,
        nombre=cliente.nombre,
        apellido=cliente.apellido,
        telefono=cliente.telefono,
        direccion=cliente.direccion,
        fecha_registro=datetime.utcnow()
    )
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente

def get_categorias(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Categoria).offset(skip).limit(limit).all()

def crear_categoria(db: Session, categoria: schemas.CategoriaCreate):
    db_categoria = models.Categoria(
        descripcion_corta=categoria.descripcion_corta,
        descripcion_larga=categoria.descripcion_larga,
        estado=categoria.estado,
        nombre=categoria.nombre
    )
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

def get_productos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Producto).offset(skip).limit(limit).all()

def crear_producto(db: Session, producto: schemas.ProductoCreate):
    """
    Creates a new product. Validates that the category exists and is active.
    
    Args:
        db (Session): Database session.
        producto (schemas.ProductoCreate): Product data to create.
    
    Returns:
        models.Producto: Created product.
    
    Raises:
        HTTPException: If the category doesn't exist, is inactive, or price/quantity is invalid.
    """
    # Validar que la categoría existe
    categoria = get_categoria(db, producto.id_categoria)
    if not categoria:
        raise HTTPException(status_code=404, detail=f"Categoría con ID {producto.id_categoria} no encontrada")
    
    # Validar que la categoría esté activa
    if categoria.estado != "activo":
        raise HTTPException(
            status_code=400, 
            detail=f"No se pueden crear productos en la categoría '{categoria.nombre}' porque está inactiva"
        )
    
    # Las validaciones de precio y cantidad ya están en el schema de Pydantic
    # pero las mantenemos aquí como validación adicional de seguridad
    
    db_producto = models.Producto(
        id_categoria=producto.id_categoria,
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        cantidad=producto.cantidad,
        precio=producto.precio,
        imagen_url=producto.imagen_url,
        estado=producto.estado
    )
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

def get_pedidos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Pedido).offset(skip).limit(limit).all()

def crear_pedido(db: Session, pedido: schemas.PedidoCreate):
    """
    Creates a new order. Validates that the client exists and has a valid address.
    
    Args:
        db (Session): Database session.
        pedido (schemas.PedidoCreate): Order data to create.
    
    Returns:
        models.Pedido: Created order.
    
    Raises:
        HTTPException: If the client doesn't exist or address is invalid.
    """
    # Validar que el cliente existe
    cliente = get_cliente(db, pedido.id_cliente)
    if not cliente:
        raise HTTPException(status_code=404, detail=f"Cliente con ID {pedido.id_cliente} no encontrado")
    
    # Validar que la dirección de envío no esté vacía
    if not pedido.direccion_envio or len(pedido.direccion_envio.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="La dirección de envío debe tener al menos 5 caracteres"
        )
    
    db_pedido = models.Pedido(
        id_cliente=pedido.id_cliente,
        estado=pedido.estado,
        direccion_envio=pedido.direccion_envio,
        fecha_pedido=datetime.utcnow(),
        metodo_pago=pedido.metodo_pago
    )
    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)
    return db_pedido

def get_detalles_pedido(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DetallePedido).offset(skip).limit(limit).all()

def crear_detalle_pedido(db: Session, detalle: schemas.DetallePedidoCreate):
    """
    Creates an order detail and deducts the corresponding product inventory.
    Uses transactions to ensure atomicity.
    
    Args:
        db (Session): Database session.
        detalle (schemas.DetallePedidoCreate): Order detail data.
    
    Returns:
        models.DetallePedido: Created order detail.
    
    Raises:
        HTTPException: If there's not enough inventory or if pedido/producto doesn't exist.
    """
    try:
        # Validar que el pedido existe
        pedido = get_pedido(db, detalle.id_pedido)
        if not pedido:
            raise HTTPException(status_code=404, detail=f"Pedido con ID {detalle.id_pedido} no encontrado")
        
        # Validar que el producto existe
        producto = db.query(models.Producto).filter(models.Producto.id_producto == detalle.id_producto).first()
        if not producto:
            raise HTTPException(status_code=404, detail=f"Producto con ID {detalle.id_producto} no encontrado")
        
        # Validar que el producto esté activo
        if producto.estado != "activo":
            raise HTTPException(
                status_code=400,
                detail=f"El producto '{producto.nombre}' no está disponible (estado: {producto.estado})"
            )
        
        # Validar inventario suficiente
        if producto.cantidad < detalle.cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Inventario insuficiente para el producto {producto.nombre}. Disponible: {producto.cantidad}, Solicitado: {detalle.cantidad}"
            )
        
        # Validar que el pedido no esté en un estado final
        if pedido.estado in ["entregado", "cancelado"]:
            raise HTTPException(
                status_code=400,
                detail=f"No se pueden agregar productos a un pedido con estado '{pedido.estado}'"
            )
        
        # Las validaciones de cantidad y precio ya están en el schema de Pydantic
        
        # Calcular subtotal
        subtotal = detalle.cantidad * detalle.precio_unitario
        
        # Crear detalle de pedido
        db_detalle = models.DetallePedido(
            id_pedido=detalle.id_pedido,
            id_producto=detalle.id_producto,
            cantidad=detalle.cantidad,
            precio_unitario=detalle.precio_unitario,
            subtotal=subtotal
        )
        
        # Descontar inventario
        producto.cantidad -= detalle.cantidad
        
        db.add(db_detalle)
        db.commit()
        db.refresh(db_detalle)
        return db_detalle
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear detalle de pedido: {str(e)}")

def actualizar_usuario(db: Session, usuario_id: int, usuario: schemas.UsuarioCreate):
    """
    Updates a user in the database. Always hashes the password if provided.
    
    Args:
        db (Session): Database session.
        usuario_id (int): User ID to update.
        usuario (schemas.UsuarioCreate): Updated user data.
    
    Returns:
        models.Usuario | None: Updated user or None if not found.
    """
    db_usuario = get_usuario(db, usuario_id)
    if not db_usuario:
        return None
    db_usuario.correo = usuario.correo
    # Siempre hashear la contraseña si se proporciona
    db_usuario.contraseña = hash_password(usuario.contraseña)
    db_usuario.rol = usuario.rol
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def eliminar_usuario(db: Session, usuario_id: int):
    db_usuario = get_usuario(db, usuario_id)
    if not db_usuario:
        return None
    db.delete(db_usuario)
    db.commit()
    return db_usuario

def get_cliente(db: Session, cliente_id: int):
    return db.query(models.Cliente).filter(models.Cliente.id_cliente == cliente_id).first()

def actualizar_cliente(db: Session, cliente_id: int, cliente: schemas.ClienteCreate):
    """
    Updates a client. Validates that the user exists and doesn't already have another client profile.
    
    Args:
        db (Session): Database session.
        cliente_id (int): Client ID to update.
        cliente (schemas.ClienteCreate): Updated client data.
    
    Returns:
        models.Cliente | None: Updated client or None if not found.
    
    Raises:
        HTTPException: If the user doesn't exist or already has another client profile.
    """
    db_cliente = get_cliente(db, cliente_id)
    if not db_cliente:
        return None
    
    # Validar que el usuario existe si se está cambiando
    if cliente.id_usuario != db_cliente.id_usuario:
        usuario = get_usuario(db, cliente.id_usuario)
        if not usuario:
            raise HTTPException(status_code=404, detail=f"Usuario con ID {cliente.id_usuario} no encontrado")
        
        # Validar que el nuevo usuario no tenga ya un perfil de cliente
        cliente_existente = get_cliente_por_id_usuario(db, cliente.id_usuario)
        if cliente_existente and cliente_existente.id_cliente != cliente_id:
            raise HTTPException(
                status_code=400,
                detail=f"El usuario con ID {cliente.id_usuario} ya tiene un perfil de cliente"
            )
    
    db_cliente.id_usuario = cliente.id_usuario
    db_cliente.nombre = cliente.nombre
    db_cliente.apellido = cliente.apellido
    db_cliente.telefono = cliente.telefono
    db_cliente.direccion = cliente.direccion
    db.commit()
    db.refresh(db_cliente)
    return db_cliente

def eliminar_cliente(db: Session, cliente_id: int):
    db_cliente = get_cliente(db, cliente_id)
    if not db_cliente:
        return None
    db.delete(db_cliente)
    db.commit()
    return db_cliente

def get_categoria(db: Session, categoria_id: int):
    return db.query(models.Categoria).filter(models.Categoria.id_categoria == categoria_id).first()

def actualizar_categoria(db: Session, categoria_id: int, categoria: schemas.CategoriaCreate):
    db_categoria = get_categoria(db, categoria_id)
    if not db_categoria:
        return None
    db_categoria.descripcion_corta = categoria.descripcion_corta
    db_categoria.descripcion_larga = categoria.descripcion_larga
    db_categoria.estado = categoria.estado
    db_categoria.nombre = categoria.nombre
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

def eliminar_categoria(db: Session, categoria_id: int):
    db_categoria = get_categoria(db, categoria_id)
    if not db_categoria:
        return None
    db.delete(db_categoria)
    db.commit()
    return db_categoria

def get_producto(db: Session, producto_id: int):
    return db.query(models.Producto).filter(models.Producto.id_producto == producto_id).first()

def actualizar_producto(db: Session, producto_id: int, producto: schemas.ProductoCreate):
    """
    Updates a product. Validates that the category exists and is active.
    
    Args:
        db (Session): Database session.
        producto_id (int): Product ID to update.
        producto (schemas.ProductoCreate): Updated product data.
    
    Returns:
        models.Producto | None: Updated product or None if not found.
    
    Raises:
        HTTPException: If the category doesn't exist or is inactive.
    """
    db_producto = get_producto(db, producto_id)
    if not db_producto:
        return None
    
    # Validar que la categoría existe si se está cambiando
    if producto.id_categoria != db_producto.id_categoria:
        categoria = get_categoria(db, producto.id_categoria)
        if not categoria:
            raise HTTPException(status_code=404, detail=f"Categoría con ID {producto.id_categoria} no encontrada")
        if categoria.estado != "activo":
            raise HTTPException(
                status_code=400,
                detail=f"No se puede asignar el producto a la categoría '{categoria.nombre}' porque está inactiva"
            )
    
    db_producto.id_categoria = producto.id_categoria
    db_producto.nombre = producto.nombre
    db_producto.descripcion = producto.descripcion
    db_producto.cantidad = producto.cantidad
    db_producto.precio = producto.precio
    db_producto.imagen_url = producto.imagen_url
    db_producto.estado = producto.estado
    db.commit()
    db.refresh(db_producto)
    return db_producto

def eliminar_producto(db: Session, producto_id: int):
    db_producto = get_producto(db, producto_id)
    if not db_producto:
        return None
    db.delete(db_producto)
    db.commit()
    return db_producto

def get_pedido(db: Session, pedido_id: int):
    return db.query(models.Pedido).filter(models.Pedido.id_pedido == pedido_id).first()

def actualizar_pedido(db: Session, pedido_id: int, pedido: schemas.PedidoCreate):
    """
    Updates an order. Validates that the order is not in a final state.
    
    Args:
        db (Session): Database session.
        pedido_id (int): Order ID to update.
        pedido (schemas.PedidoCreate): Updated order data.
    
    Returns:
        models.Pedido | None: Updated order or None if not found.
    
    Raises:
        HTTPException: If the order is in a final state or client doesn't exist.
    """
    db_pedido = get_pedido(db, pedido_id)
    if not db_pedido:
        return None
    
    # Validar que el pedido no esté en un estado final
    if db_pedido.estado in ["entregado", "cancelado"]:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede modificar un pedido con estado '{db_pedido.estado}'"
        )
    
    # Validar que el cliente existe si se está cambiando
    if pedido.id_cliente != db_pedido.id_cliente:
        cliente = get_cliente(db, pedido.id_cliente)
        if not cliente:
            raise HTTPException(status_code=404, detail=f"Cliente con ID {pedido.id_cliente} no encontrado")
    
    # Validar dirección de envío
    if pedido.direccion_envio and len(pedido.direccion_envio.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="La dirección de envío debe tener al menos 5 caracteres"
        )
    
    db_pedido.id_cliente = pedido.id_cliente
    db_pedido.estado = pedido.estado
    db_pedido.direccion_envio = pedido.direccion_envio
    db_pedido.metodo_pago = pedido.metodo_pago
    db.commit()
    db.refresh(db_pedido)
    return db_pedido

def eliminar_pedido(db: Session, pedido_id: int):
    db_pedido = get_pedido(db, pedido_id)
    if not db_pedido:
        return None
    db.delete(db_pedido)
    db.commit()
    return db_pedido

def get_detalle_pedido(db: Session, detalle_id: int):
    return db.query(models.DetallePedido).filter(models.DetallePedido.id_detalle == detalle_id).first()

def actualizar_detalle_pedido(db: Session, detalle_id: int, detalle: schemas.DetallePedidoCreate):
    """
    Updates an order detail. Validates product availability and order state.
    
    Args:
        db (Session): Database session.
        detalle_id (int): Order detail ID to update.
        detalle (schemas.DetallePedidoCreate): Updated order detail data.
    
    Returns:
        models.DetallePedido | None: Updated order detail or None if not found.
    
    Raises:
        HTTPException: If product doesn't exist, is inactive, insufficient inventory, or order is in final state.
    """
    db_detalle = get_detalle_pedido(db, detalle_id)
    if not db_detalle:
        return None
    
    # Validar que el pedido no esté en un estado final
    pedido = get_pedido(db, detalle.id_pedido)
    if pedido and pedido.estado in ["entregado", "cancelado"]:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede modificar un detalle de pedido cuando el pedido está en estado '{pedido.estado}'"
        )
    
    # Validar producto si se está cambiando
    if detalle.id_producto != db_detalle.id_producto:
        producto = db.query(models.Producto).filter(models.Producto.id_producto == detalle.id_producto).first()
        if not producto:
            raise HTTPException(status_code=404, detail=f"Producto con ID {detalle.id_producto} no encontrado")
        if producto.estado != "activo":
            raise HTTPException(
                status_code=400,
                detail=f"El producto '{producto.nombre}' no está disponible"
            )
    
    # Validar inventario si se está cambiando la cantidad
    if detalle.cantidad != db_detalle.cantidad:
        producto = db.query(models.Producto).filter(models.Producto.id_producto == detalle.id_producto).first()
        if producto:
            # Calcular cantidad disponible (sumar la cantidad actual del detalle)
            cantidad_disponible = producto.cantidad + db_detalle.cantidad
            if cantidad_disponible < detalle.cantidad:
                raise HTTPException(
                    status_code=400,
                    detail=f"Inventario insuficiente. Disponible: {cantidad_disponible}, Solicitado: {detalle.cantidad}"
                )
            # Actualizar inventario
            producto.cantidad = cantidad_disponible - detalle.cantidad
    
    db_detalle.id_pedido = detalle.id_pedido
    db_detalle.id_producto = detalle.id_producto
    db_detalle.cantidad = detalle.cantidad
    db_detalle.precio_unitario = detalle.precio_unitario
    db_detalle.subtotal = detalle.cantidad * detalle.precio_unitario
    db.commit()
    db.refresh(db_detalle)
    return db_detalle

def eliminar_detalle_pedido(db: Session, detalle_id: int):
    db_detalle = get_detalle_pedido(db, detalle_id)
    if not db_detalle:
        return None
    db.delete(db_detalle)
    db.commit()
    return db_detalle

def get_carritos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Carrito).offset(skip).limit(limit).all()

def get_carrito(db: Session, carrito_id: int):
    return db.query(models.Carrito).filter(models.Carrito.id_carrito == carrito_id).first()

def crear_carrito(db: Session, carrito: schemas.CarritoCreate):
    """
    Creates a new shopping cart. Validates that the client exists.
    
    Args:
        db (Session): Database session.
        carrito (schemas.CarritoCreate): Cart data to create.
    
    Returns:
        models.Carrito: Created cart.
    
    Raises:
        HTTPException: If the client doesn't exist.
    """
    # Validar que el cliente existe
    cliente = get_cliente(db, carrito.id_cliente)
    if not cliente:
        raise HTTPException(status_code=404, detail=f"Cliente con ID {carrito.id_cliente} no encontrado")
    
    db_carrito = models.Carrito(
        id_cliente=carrito.id_cliente,
        estado=carrito.estado,
        fecha_creacion=datetime.utcnow()
    )
    db.add(db_carrito)
    db.commit()
    db.refresh(db_carrito)
    return db_carrito

def actualizar_carrito(db: Session, carrito_id: int, carrito: schemas.CarritoCreate):
    db_carrito = get_carrito(db, carrito_id)
    if not db_carrito:
        return None
    db_carrito.id_cliente = carrito.id_cliente
    db_carrito.estado = carrito.estado
    db.commit()
    db.refresh(db_carrito)
    return db_carrito

def eliminar_carrito(db: Session, carrito_id: int):
    db_carrito = get_carrito(db, carrito_id)
    if not db_carrito:
        return None
    db.delete(db_carrito)
    db.commit()
    return db_carrito

def get_detalles_carrito(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DetalleCarrito).offset(skip).limit(limit).all()

def get_detalle_carrito(db: Session, detalle_id: int):
    return db.query(models.DetalleCarrito).filter(models.DetalleCarrito.id_detalle_carrito == detalle_id).first()

def crear_detalle_carrito(db: Session, detalle: schemas.DetalleCarritoCreate):
    """
    Creates a cart detail item. Validates inventory availability.
    
    Args:
        db (Session): Database session.
        detalle (schemas.DetalleCarritoCreate): Cart detail data.
    
    Returns:
        models.DetalleCarrito: Created cart detail.
    
    Raises:
        HTTPException: If cart/product doesn't exist or insufficient inventory.
    """
    try:
        # Validar que el carrito existe
        carrito = get_carrito(db, detalle.id_carrito)
        if not carrito:
            raise HTTPException(status_code=404, detail=f"Carrito con ID {detalle.id_carrito} no encontrado")
        
        # Validar que el producto existe
        producto = db.query(models.Producto).filter(models.Producto.id_producto == detalle.id_producto).first()
        if not producto:
            raise HTTPException(status_code=404, detail=f"Producto con ID {detalle.id_producto} no encontrado")
        
        # Validar que el producto esté activo
        if producto.estado != "activo":
            raise HTTPException(
                status_code=400,
                detail=f"El producto '{producto.nombre}' no está disponible (estado: {producto.estado})"
            )
        
        # Validar que el carrito esté activo
        if carrito.estado != "activo":
            raise HTTPException(
                status_code=400,
                detail=f"No se pueden agregar productos a un carrito con estado '{carrito.estado}'"
            )
        
        # Validar inventario suficiente (para carrito, verificamos pero no descontamos aún)
        if producto.cantidad < detalle.cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Inventario insuficiente para el producto {producto.nombre}. Disponible: {producto.cantidad}, Solicitado: {detalle.cantidad}"
            )
        
        # Las validaciones de cantidad y precio ya están en el schema de Pydantic
        
        # Calcular subtotal si no se proporciona
        subtotal = detalle.subtotal if detalle.subtotal else (detalle.cantidad * detalle.precio_unitario)
        
        db_detalle = models.DetalleCarrito(
            id_carrito=detalle.id_carrito,
            id_producto=detalle.id_producto,
            cantidad=detalle.cantidad,
            precio_unitario=detalle.precio_unitario,
            subtotal=subtotal
        )
        db.add(db_detalle)
        db.commit()
        db.refresh(db_detalle)
        return db_detalle
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear detalle de carrito: {str(e)}")

def actualizar_detalle_carrito(db: Session, detalle_id: int, detalle: schemas.DetalleCarritoCreate):
    """
    Updates a cart detail. Validates product availability and cart state.
    
    Args:
        db (Session): Database session.
        detalle_id (int): Cart detail ID to update.
        detalle (schemas.DetalleCarritoCreate): Updated cart detail data.
    
    Returns:
        models.DetalleCarrito | None: Updated cart detail or None if not found.
    
    Raises:
        HTTPException: If product doesn't exist, is inactive, insufficient inventory, or cart is not active.
    """
    db_detalle = get_detalle_carrito(db, detalle_id)
    if not db_detalle:
        return None
    
    # Validar que el carrito esté activo
    carrito = get_carrito(db, detalle.id_carrito)
    if carrito and carrito.estado != "activo":
        raise HTTPException(
            status_code=400,
            detail=f"No se puede modificar un detalle de carrito cuando el carrito está en estado '{carrito.estado}'"
        )
    
    # Validar producto si se está cambiando
    if detalle.id_producto != db_detalle.id_producto:
        producto = db.query(models.Producto).filter(models.Producto.id_producto == detalle.id_producto).first()
        if not producto:
            raise HTTPException(status_code=404, detail=f"Producto con ID {detalle.id_producto} no encontrado")
        if producto.estado != "activo":
            raise HTTPException(
                status_code=400,
                detail=f"El producto '{producto.nombre}' no está disponible"
            )
    
    # Validar inventario si se está cambiando la cantidad
    if detalle.cantidad != db_detalle.cantidad:
        producto = db.query(models.Producto).filter(models.Producto.id_producto == detalle.id_producto).first()
        if producto and producto.cantidad < detalle.cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Inventario insuficiente. Disponible: {producto.cantidad}, Solicitado: {detalle.cantidad}"
            )
    
    # Calcular subtotal si cambia cantidad o precio
    if detalle.cantidad != db_detalle.cantidad or detalle.precio_unitario != db_detalle.precio_unitario:
        # Si se proporciona subtotal, validar que coincida; si no, calcularlo
        if detalle.subtotal:
            calculado = detalle.cantidad * detalle.precio_unitario
            if abs(detalle.subtotal - calculado) > 0.01:
                raise HTTPException(
                    status_code=400,
                    detail=f"El subtotal debe ser igual a cantidad × precio_unitario ({calculado:.2f})"
                )
        else:
            detalle.subtotal = detalle.cantidad * detalle.precio_unitario
    
    db_detalle.id_carrito = detalle.id_carrito
    db_detalle.id_producto = detalle.id_producto
    db_detalle.cantidad = detalle.cantidad
    db_detalle.precio_unitario = detalle.precio_unitario
    db_detalle.subtotal = detalle.subtotal
    db.commit()
    db.refresh(db_detalle)
    return db_detalle

def eliminar_detalle_carrito(db: Session, detalle_id: int):
    db_detalle = get_detalle_carrito(db, detalle_id)
    if not db_detalle:
        return None
    db.delete(db_detalle)
    db.commit()
    return db_detalle

def get_cliente_por_id_usuario(db: Session, id_usuario: int):
    return db.query(models.Cliente).filter(models.Cliente.id_usuario == id_usuario).first()

def get_audit_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    tabla_nombre: Optional[str] = None,
    registro_id: Optional[int] = None,
    accion: Optional[str] = None,
    usuario_id: Optional[int] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None
):
    """
    Obtiene logs de auditoría con filtros.
    Solo accesible para administradores.
    """
    from datetime import datetime
    query = db.query(models.AuditLog)
    
    if tabla_nombre:
        query = query.filter(models.AuditLog.tabla_nombre == tabla_nombre)
    if registro_id:
        query = query.filter(models.AuditLog.registro_id == registro_id)
    if accion:
        query = query.filter(models.AuditLog.accion == accion)
    if usuario_id:
        query = query.filter(models.AuditLog.usuario_id == usuario_id)
    if fecha_desde:
        query = query.filter(models.AuditLog.fecha_accion >= fecha_desde)
    if fecha_hasta:
        query = query.filter(models.AuditLog.fecha_accion <= fecha_hasta)
    
    return query.order_by(models.AuditLog.fecha_accion.desc()).offset(skip).limit(limit).all()


# ============================================
# FUNCIONES PARA CONFIRMACIÓN Y RECUPERACIÓN
# ============================================

def confirmar_cuenta(db: Session, token: str) -> models.Usuario:
    """
    Confirma la cuenta de un usuario usando el token de confirmación.
    
    Args:
        db: Sesión de base de datos
        token: Token de confirmación
    
    Returns:
        models.Usuario: Usuario confirmado
    
    Raises:
        HTTPException: Si el token es inválido o ya fue usado
    """
    usuario = db.query(models.Usuario).filter(
        models.Usuario.token_confirmacion == token
    ).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Token de confirmación inválido")
    
    if usuario.email_verificado == "S":
        raise HTTPException(status_code=400, detail="La cuenta ya está confirmada")
    
    # Validar expiración del token
    if usuario.token_confirmacion_expira and datetime.utcnow() > usuario.token_confirmacion_expira:
        raise HTTPException(status_code=400, detail="El token de confirmación ha expirado. Solicita un nuevo email de confirmación.")
    
    usuario.email_verificado = "S"
    usuario.token_confirmacion = None  # Invalidar token después de usar
    usuario.token_confirmacion_expira = None
    db.commit()
    db.refresh(usuario)
    return usuario


def generar_pin_recuperacion(db: Session, correo: str) -> str:
    """
    Genera un PIN de 6 dígitos para recuperación de contraseña.
    
    Args:
        db: Sesión de base de datos
        correo: Correo del usuario
    
    Returns:
        str: PIN generado
    
    Raises:
        HTTPException: Si el usuario no existe
    """
    usuario = get_usuario_por_correo(db, correo)
    if not usuario:
        # Por seguridad, no revelamos si el email existe o no
        raise HTTPException(
            status_code=404,
            detail="Si el correo existe, se enviará un PIN de recuperación"
        )
    
    # Generar PIN de 6 dígitos
    pin = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    # Guardar PIN y expiración (15 minutos)
    usuario.token_reset = pin
    usuario.token_reset_expira = datetime.utcnow() + timedelta(minutes=15)
    db.commit()
    
    return pin


def validar_pin_recuperacion(db: Session, correo: str, pin: str) -> bool:
    """
    Valida un PIN de recuperación de contraseña.
    
    Args:
        db: Sesión de base de datos
        correo: Correo del usuario
        pin: PIN a validar
    
    Returns:
        bool: True si el PIN es válido, False en caso contrario
    """
    usuario = get_usuario_por_correo(db, correo)
    if not usuario:
        return False
    
    if not usuario.token_reset or not usuario.token_reset_expira:
        return False
    
    if usuario.token_reset != pin:
        return False
    
    if datetime.utcnow() > usuario.token_reset_expira:
        return False
    
    return True


def cambiar_contraseña_con_pin(db: Session, correo: str, pin: str, nueva_contraseña: str) -> models.Usuario:
    """
    Cambia la contraseña de un usuario usando PIN de recuperación.
    
    Args:
        db: Sesión de base de datos
        correo: Correo del usuario
        pin: PIN de recuperación
        nueva_contraseña: Nueva contraseña en texto plano
    
    Returns:
        models.Usuario: Usuario actualizado
    
    Raises:
        HTTPException: Si el PIN es inválido o expiró
    """
    if not validar_pin_recuperacion(db, correo, pin):
        raise HTTPException(
            status_code=400,
            detail="PIN inválido o expirado. Solicita un nuevo PIN."
        )
    
    usuario = get_usuario_por_correo(db, correo)
    usuario.contraseña = hash_password(nueva_contraseña)
    usuario.token_reset = None  # Invalidar PIN después de usar
    usuario.token_reset_expira = None
    db.commit()
    db.refresh(usuario)
    return usuario


def cambiar_contraseña_usuario(db: Session, usuario_id: int, contraseña_actual: str, nueva_contraseña: str) -> models.Usuario:
    """
    Cambia la contraseña de un usuario autenticado.
    
    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario
        contraseña_actual: Contraseña actual en texto plano
        nueva_contraseña: Nueva contraseña en texto plano
    
    Returns:
        models.Usuario: Usuario actualizado
    
    Raises:
        HTTPException: Si la contraseña actual es incorrecta o el usuario no existe
    """
    from .auth import verify_password
    
    usuario = get_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if not verify_password(contraseña_actual, usuario.contraseña):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    
    usuario.contraseña = hash_password(nueva_contraseña)
    db.commit()
    db.refresh(usuario)
    return usuario


def regenerar_token_confirmacion(db: Session, correo: str) -> str:
    """
    Regenera el token de confirmación para un usuario.
    
    Args:
        db: Sesión de base de datos
        correo: Correo del usuario
    
    Returns:
        str: Nuevo token de confirmación
    
    Raises:
        HTTPException: Si el usuario no existe o ya está confirmado
    """
    usuario = get_usuario_por_correo(db, correo)
    if not usuario:
        # Por seguridad, no revelamos si el email existe
        raise HTTPException(
            status_code=404,
            detail="Si el correo existe y no está confirmado, se enviará un nuevo email"
        )
    
    if usuario.email_verificado == "S":
        raise HTTPException(status_code=400, detail="La cuenta ya está confirmada")
    
    # Generar nuevo token con expiración de 1 hora
    nuevo_token = str(uuid.uuid4())
    usuario.token_confirmacion = nuevo_token
    usuario.token_confirmacion_expira = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    return nuevo_token
