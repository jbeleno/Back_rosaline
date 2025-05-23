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
from . import models, schemas
from datetime import datetime
from .auth import hash_password


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
    Creates a new user in the database with a hashed password.

    Args:
        db (Session): Database session.
        usuario (schemas.UsuarioCreate): User data to create.

    Returns:
        models.Usuario: Created user.
    """
    db_usuario = models.Usuario(
        correo=usuario.correo,
        contraseña=hash_password(usuario.contraseña),
        rol=usuario.rol,
        fecha_creacion=datetime.utcnow()
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def get_clientes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Cliente).offset(skip).limit(limit).all()

def crear_cliente(db: Session, cliente: schemas.ClienteCreate):
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
    Raises an exception if there is not enough inventory.
    """
    subtotal = detalle.cantidad * detalle.precio_unitario
    db_detalle = models.DetallePedido(
        id_pedido=detalle.id_pedido,
        id_producto=detalle.id_producto,
        cantidad=detalle.cantidad,
        precio_unitario=detalle.precio_unitario,
        subtotal=subtotal
    )
    # Deduct the quantity from the product inventory
    producto = db.query(models.Producto).filter(models.Producto.id_producto == detalle.id_producto).first()
    if producto:
        if producto.cantidad >= detalle.cantidad:
            producto.cantidad -= detalle.cantidad
        else:
            raise Exception(f"Not enough inventory for product: {producto.nombre}")
    db.add(db_detalle)
    db.commit()
    db.refresh(db_detalle)
    return db_detalle

def actualizar_usuario(db: Session, usuario_id: int, usuario: schemas.UsuarioCreate):
    db_usuario = get_usuario(db, usuario_id)
    if not db_usuario:
        return None
    db_usuario.correo = usuario.correo
    db_usuario.contraseña = usuario.contraseña
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
    db_cliente = get_cliente(db, cliente_id)
    if not db_cliente:
        return None
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
    db_producto = get_producto(db, producto_id)
    if not db_producto:
        return None
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
    db_pedido = get_pedido(db, pedido_id)
    if not db_pedido:
        return None
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
    db_detalle = get_detalle_pedido(db, detalle_id)
    if not db_detalle:
        return None
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
    db_detalle = models.DetalleCarrito(
        id_carrito=detalle.id_carrito,
        id_producto=detalle.id_producto,
        cantidad=detalle.cantidad,
        precio_unitario=detalle.precio_unitario,
        subtotal=detalle.subtotal
    )
    db.add(db_detalle)
    db.commit()
    db.refresh(db_detalle)
    return db_detalle

def actualizar_detalle_carrito(db: Session, detalle_id: int, detalle: schemas.DetalleCarritoCreate):
    db_detalle = get_detalle_carrito(db, detalle_id)
    if not db_detalle:
        return None
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
