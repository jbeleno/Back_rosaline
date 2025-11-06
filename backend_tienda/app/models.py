"""
Definition of SQLAlchemy ORM models for the database.

Includes the tables for users, clients, categories, products, orders, carts, and their details.
Main dependency: SQLAlchemy
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, TIMESTAMP, Computed
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True, index=True)
    correo = Column(String(255), unique=True, nullable=False)
    contraseña = Column(String(255), nullable=False)
    rol = Column(String(50), nullable=False, default="cliente")
    fecha_creacion = Column(TIMESTAMP, nullable=False)

class Cliente(Base):
    __tablename__ = "clientes"
    id_cliente = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    nombre = Column(String(255), nullable=False)
    apellido = Column(String(255), nullable=False)
    telefono = Column(String(15))
    direccion = Column(Text)
    fecha_registro = Column(TIMESTAMP)
    usuario = relationship("Usuario")

class Categoria(Base):
    __tablename__ = "categorias"
    id_categoria = Column(Integer, primary_key=True, index=True)
    descripcion_corta = Column(String(255), nullable=False)
    descripcion_larga = Column(Text)
    estado = Column(String(20), default="activo")
    nombre = Column(String(255), nullable=False)

class Producto(Base):
    __tablename__ = "productos"
    id_producto = Column(Integer, primary_key=True, index=True)
    id_categoria = Column(Integer, ForeignKey("categorias.id_categoria"), nullable=False)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=False)
    cantidad = Column(Integer, nullable=False, default=0)
    precio = Column(Numeric(10, 2), nullable=False)
    imagen_url = Column(String(255))
    estado = Column(String(20), default="activo")
    categoria = relationship("Categoria")

class Pedido(Base):
    __tablename__ = "pedidos"
    id_pedido = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey("clientes.id_cliente"), nullable=False)
    estado = Column(String(20), default="pendiente")
    direccion_envio = Column(Text, nullable=False)
    fecha_pedido = Column(TIMESTAMP)
    metodo_pago = Column(String(50), default="PayPal")
    cliente = relationship("Cliente")

class DetallePedido(Base):
    __tablename__ = "detalle_pedidos"
    id_detalle = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id_pedido"), nullable=False)
    id_producto = Column(Integer, ForeignKey("productos.id_producto"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2))
    pedido = relationship("Pedido")
    producto = relationship("Producto")

class Carrito(Base):
    __tablename__ = "carrito"
    id_carrito = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey("clientes.id_cliente"), nullable=False)
    fecha_creacion = Column(TIMESTAMP)
    estado = Column(String(20), default="activo")
    cliente = relationship("Cliente")

class DetalleCarrito(Base):
    __tablename__ = "detalle_carrito"
    id_detalle_carrito = Column(Integer, primary_key=True, index=True)
    id_carrito = Column(Integer, ForeignKey("carrito.id_carrito"), nullable=False)
    id_producto = Column(Integer, ForeignKey("productos.id_producto"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2))
    carrito = relationship("Carrito")
    producto = relationship("Producto")

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id_audit = Column(Integer, primary_key=True, index=True)
    tabla_nombre = Column(String(100), nullable=False, index=True)
    registro_id = Column(Integer, nullable=False, index=True)
    accion = Column(String(10), nullable=False, index=True)  # INSERT, UPDATE, DELETE
    usuario_id = Column(Integer, ForeignKey("usuarios.id_usuario"), index=True, nullable=True)
    usuario_email = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    endpoint = Column(String(255), nullable=True)
    datos_anteriores = Column(JSONB, nullable=True)
    datos_nuevos = Column(JSONB, nullable=True)
    cambios = Column(JSONB, nullable=True)  # Solo campos que cambiaron
    fecha_accion = Column(TIMESTAMP, nullable=False, index=True)
    metadata = Column(JSONB, nullable=True)  # Información adicional
    
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
