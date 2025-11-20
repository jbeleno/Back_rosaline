"""
Definition of SQLAlchemy ORM models for the database.

Includes the tables for users, clients, categories, products, orders, carts, and their details.
Main dependency: SQLAlchemy
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, TIMESTAMP, Computed, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True, index=True)
    correo = Column(String(255), unique=True, nullable=False, index=True)
    contraseña = Column(String(255), nullable=False)
    rol = Column(String(50), nullable=False, default="cliente")
    fecha_creacion = Column(TIMESTAMP, nullable=False)
    email_verificado = Column(String(1), default="N", nullable=False)  # 'S' o 'N'
    token_confirmacion = Column(String(6), nullable=True, index=True)  # PIN de 6 dígitos para confirmar email
    token_confirmacion_expira = Column(TIMESTAMP, nullable=True)  # Expiración del PIN (15 minutos)
    token_reset = Column(String(6), nullable=True)  # PIN de 6 dígitos para reset de contraseña
    token_reset_expira = Column(TIMESTAMP, nullable=True)  # Expiración del PIN (15 minutos)
    
    __table_args__ = (
        CheckConstraint("rol IN ('cliente', 'admin', 'super_admin')", name="check_rol_valido"),
        CheckConstraint("email_verificado IN ('S', 'N')", name="check_email_verificado"),
    )

class Cliente(Base):
    __tablename__ = "clientes"
    id_cliente = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False, unique=True, index=True)
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
    estado = Column(String(20), default="activo", index=True)
    nombre = Column(String(255), nullable=False)
    
    __table_args__ = (
        CheckConstraint("estado IN ('activo', 'inactivo')", name="check_categoria_estado"),
    )

class Producto(Base):
    __tablename__ = "productos"
    id_producto = Column(Integer, primary_key=True, index=True)
    id_categoria = Column(Integer, ForeignKey("categorias.id_categoria"), nullable=False, index=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=False)
    cantidad = Column(Integer, nullable=False, default=0)
    precio = Column(Numeric(10, 2), nullable=False)
    imagen_url = Column(String(255))
    estado = Column(String(20), default="activo", index=True)
    categoria = relationship("Categoria")
    
    __table_args__ = (
        CheckConstraint("precio > 0", name="check_precio_positivo"),
        CheckConstraint("cantidad >= 0", name="check_cantidad_no_negativa"),
        CheckConstraint("estado IN ('activo', 'inactivo')", name="check_producto_estado"),
        Index("idx_producto_categoria_estado", "id_categoria", "estado"),  # Índice compuesto para búsquedas frecuentes
    )

class Pedido(Base):
    __tablename__ = "pedidos"
    id_pedido = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey("clientes.id_cliente", ondelete="CASCADE"), nullable=False, index=True)
    estado = Column(String(20), default="pendiente", index=True)
    direccion_envio = Column(Text, nullable=False)
    fecha_pedido = Column(TIMESTAMP, index=True)
    metodo_pago = Column(String(50), default="PayPal")
    cliente = relationship("Cliente")
    
    __table_args__ = (
        CheckConstraint("estado IN ('pendiente', 'Pago confirmado', 'En preparación', 'En domicilio', 'Listo para recoger', 'Entregado')", name="check_pedido_estado"),
        CheckConstraint("metodo_pago IN ('PayPal', 'Tarjeta', 'Efectivo')", name="check_metodo_pago"),
        Index("idx_pedido_cliente_estado", "id_cliente", "estado"),  # Para listar pedidos de un cliente por estado
        Index("idx_pedido_fecha_estado", "fecha_pedido", "estado"),  # Para ordenar y filtrar pedidos
    )

class DetallePedido(Base):
    __tablename__ = "detalle_pedidos"
    id_detalle = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id_pedido", ondelete="CASCADE"), nullable=False, index=True)
    id_producto = Column(Integer, ForeignKey("productos.id_producto"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2))
    pedido = relationship("Pedido")
    producto = relationship("Producto")
    
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="check_detalle_pedido_cantidad"),
        CheckConstraint("cantidad <= 1000", name="check_detalle_pedido_cantidad_max"),
        CheckConstraint("precio_unitario > 0", name="check_detalle_pedido_precio"),
        CheckConstraint("subtotal >= 0", name="check_detalle_pedido_subtotal"),
        # El subtotal se calcula automáticamente, pero validamos que sea >= 0
    )

class Carrito(Base):
    __tablename__ = "carrito"
    id_carrito = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey("clientes.id_cliente", ondelete="CASCADE"), nullable=False, index=True)
    fecha_creacion = Column(TIMESTAMP)
    estado = Column(String(20), default="activo", index=True)
    cliente = relationship("Cliente")
    
    __table_args__ = (
        CheckConstraint("estado IN ('activo', 'inactivo', 'completado')", name="check_carrito_estado"),
        Index("idx_carrito_cliente_estado", "id_cliente", "estado"),  # Para buscar carrito activo de un cliente
    )

class DetalleCarrito(Base):
    __tablename__ = "detalle_carrito"
    id_detalle_carrito = Column(Integer, primary_key=True, index=True)
    id_carrito = Column(Integer, ForeignKey("carrito.id_carrito", ondelete="CASCADE"), nullable=False, index=True)
    id_producto = Column(Integer, ForeignKey("productos.id_producto"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2))
    carrito = relationship("Carrito")
    producto = relationship("Producto")
    
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="check_detalle_carrito_cantidad"),
        CheckConstraint("cantidad <= 1000", name="check_detalle_carrito_cantidad_max"),
        CheckConstraint("precio_unitario > 0", name="check_detalle_carrito_precio"),
        CheckConstraint("subtotal >= 0", name="check_detalle_carrito_subtotal"),
    )

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id_audit = Column(Integer, primary_key=True, index=True)
    tabla_nombre = Column(String(100), nullable=False, index=True)
    registro_id = Column(Integer, nullable=False, index=True)
    accion = Column(String(10), nullable=False, index=True)  # INSERT, UPDATE, DELETE
    usuario_id = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="SET NULL"), index=True, nullable=True)
    usuario_email = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    endpoint = Column(String(255), nullable=True)
    datos_anteriores = Column(JSONB, nullable=True)
    datos_nuevos = Column(JSONB, nullable=True)
    cambios = Column(JSONB, nullable=True)  # Solo campos que cambiaron
    fecha_accion = Column(TIMESTAMP, nullable=False, index=True)
    metadatos_extra = Column("metadata", JSONB, nullable=True)  # Información adicional (nombre columna DB: metadata)
    
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
