"""
Data validation and serialization schemas using Pydantic for the API.

Includes the models for user, client, category, product, order, cart, and their details.
Main dependencies: Pydantic, typing, datetime
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UsuarioBase(BaseModel):
    correo: str
    rol: Optional[str] = "cliente"

class UsuarioCreate(UsuarioBase):
    contraseña: str

class Usuario(UsuarioBase):
    id_usuario: int
    fecha_creacion: datetime
    class Config:
        from_attributes = True

class ClienteBase(BaseModel):
    nombre: str
    apellido: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None

class ClienteCreate(ClienteBase):
    id_usuario: int

class Cliente(ClienteBase):
    id_cliente: int
    fecha_registro: datetime
    usuario: Usuario
    class Config:
        from_attributes = True

class CategoriaBase(BaseModel):
    descripcion_corta: str
    descripcion_larga: Optional[str] = None
    estado: Optional[str] = "activo"
    nombre: str

class CategoriaCreate(CategoriaBase):
    pass

class Categoria(CategoriaBase):
    id_categoria: int
    class Config:
        from_attributes = True

class ProductoBase(BaseModel):
    id_categoria: int
    nombre: str
    descripcion: str
    cantidad: int
    precio: float
    imagen_url: Optional[str] = None
    estado: Optional[str] = "activo"

class ProductoCreate(ProductoBase):
    pass

class Producto(ProductoBase):
    id_producto: int
    categoria: Categoria
    class Config:
        from_attributes = True

class PedidoBase(BaseModel):
    id_cliente: int
    estado: Optional[str] = "pendiente"
    direccion_envio: str
    metodo_pago: Optional[str] = "PayPal"

class PedidoCreate(PedidoBase):
    pass

class Pedido(PedidoBase):
    id_pedido: int
    fecha_pedido: datetime
    cliente: Cliente
    class Config:
        from_attributes = True

class DetallePedidoBase(BaseModel):
    id_pedido: int
    id_producto: int
    cantidad: int
    precio_unitario: float

class DetallePedidoCreate(DetallePedidoBase):
    pass

class DetallePedido(DetallePedidoBase):
    id_detalle: int
    subtotal: float
    pedido: Pedido
    producto: Producto
    class Config:
        from_attributes = True

class CarritoBase(BaseModel):
    id_cliente: int
    estado: Optional[str] = "activo"

class CarritoCreate(CarritoBase):
    pass

class Carrito(CarritoBase):
    id_carrito: int
    fecha_creacion: datetime
    cliente: Cliente
    class Config:
        from_attributes = True

class DetalleCarritoBase(BaseModel):
    id_carrito: int
    id_producto: int
    cantidad: int
    precio_unitario: float
    subtotal: float

class DetalleCarritoCreate(DetalleCarritoBase):
    pass

class DetalleCarrito(DetalleCarritoBase):
    id_detalle_carrito: int
    subtotal: float
    carrito: Carrito
    producto: Producto
    class Config:
        from_attributes = True

class AuditLogBase(BaseModel):
    tabla_nombre: str
    registro_id: int
    accion: str
    usuario_id: Optional[int] = None
    usuario_email: Optional[str] = None
    ip_address: Optional[str] = None
    endpoint: Optional[str] = None
    fecha_accion: datetime

class AuditLog(AuditLogBase):
    id_audit: int
    datos_anteriores: Optional[dict] = None
    datos_nuevos: Optional[dict] = None
    cambios: Optional[dict] = None
    metadata: Optional[dict] = None
    
    class Config:
        from_attributes = True