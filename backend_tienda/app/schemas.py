"""
Data validation and serialization schemas using Pydantic for the API.

Includes the models for user, client, category, product, order, cart, and their details.
Main dependencies: Pydantic, typing, datetime
"""

from pydantic import BaseModel, EmailStr, Field, validator, constr
from typing import Optional
from datetime import datetime
from enum import Enum

class UsuarioBase(BaseModel):
    correo: EmailStr = Field(..., description="Correo electrónico del usuario")
    rol: Optional[str] = Field(default="cliente")

class UsuarioCreate(UsuarioBase):
    contraseña: constr(min_length=8, max_length=100) = Field(
        ...,
        description="Contraseña del usuario (mínimo 8 caracteres)",
        example="miPassword123"
    )
    
    @validator('contraseña')
    def validar_contraseña(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v
    
    @validator('rol')
    def validar_rol(cls, v):
        if v and v not in ['cliente', 'admin']:
            raise ValueError('El rol debe ser "cliente" o "admin"')
        return v or 'cliente'
    
    class Config:
        schema_extra = {
            "example": {
                "correo": "cliente@ejemplo.com",
                "contraseña": "miPassword123",
                "rol": "cliente"
            }
        }

class Usuario(UsuarioBase):
    id_usuario: int
    fecha_creacion: datetime
    email_verificado: Optional[str] = "N"
    class Config:
        from_attributes = True

# Schemas para confirmación de cuenta
class ConfirmarCuentaRequest(BaseModel):
    token: str = Field(..., description="Token de confirmación recibido por email")

class ConfirmarCuentaResponse(BaseModel):
    mensaje: str
    email_verificado: bool

# Schemas para recuperación de contraseña
class SolicitarRecuperacionRequest(BaseModel):
    correo: EmailStr = Field(..., description="Correo electrónico del usuario")

class SolicitarRecuperacionResponse(BaseModel):
    mensaje: str

class ValidarPinRequest(BaseModel):
    correo: EmailStr = Field(..., description="Correo electrónico del usuario")
    pin: constr(min_length=6, max_length=6, pattern=r'^\d{6}$') = Field(..., description="PIN de 6 dígitos")

class ValidarPinResponse(BaseModel):
    valido: bool
    mensaje: str

class CambiarContraseñaRequest(BaseModel):
    correo: EmailStr = Field(..., description="Correo electrónico del usuario")
    pin: constr(min_length=6, max_length=6, pattern=r'^\d{6}$') = Field(..., description="PIN de 6 dígitos")
    nueva_contraseña: constr(min_length=8, max_length=100) = Field(..., description="Nueva contraseña")
    
    @validator('nueva_contraseña')
    def validar_contraseña(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v

class CambiarContraseñaResponse(BaseModel):
    mensaje: str

# Schema para cambio de contraseña de usuario autenticado
class CambiarContraseñaAutenticadoRequest(BaseModel):
    contraseña_actual: str = Field(..., description="Contraseña actual")
    nueva_contraseña: constr(min_length=8, max_length=100) = Field(..., description="Nueva contraseña")
    
    @validator('nueva_contraseña')
    def validar_contraseña(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v

class CambiarContraseñaAutenticadoResponse(BaseModel):
    mensaje: str

# Schema para reenviar email de confirmación
class ReenviarConfirmacionRequest(BaseModel):
    correo: EmailStr = Field(..., description="Correo electrónico del usuario")

class ReenviarConfirmacionResponse(BaseModel):
    mensaje: str

class ClienteBase(BaseModel):
    nombre: constr(min_length=1, max_length=100, strip_whitespace=True)
    apellido: constr(min_length=1, max_length=100, strip_whitespace=True)
    telefono: Optional[constr(max_length=20, pattern=r'^\+?[\d\s-]+$')] = None
    direccion: Optional[constr(max_length=255)] = None
    
    @validator('nombre', 'apellido')
    def validar_nombre(cls, v):
        if not v or not v.strip():
            raise ValueError('El nombre y apellido son requeridos y no pueden estar vacíos')
        return v.strip()

class ClienteCreate(ClienteBase):
    id_usuario: int = Field(gt=0, description="ID del usuario asociado")
    
    class Config:
        schema_extra = {
            "example": {
                "id_usuario": 1,
                "nombre": "Juan",
                "apellido": "Pérez",
                "telefono": "+1234567890",
                "direccion": "Calle Principal 123"
            }
        }

class Cliente(ClienteBase):
    id_cliente: int
    fecha_registro: datetime
    usuario: Usuario
    class Config:
        from_attributes = True

class CategoriaBase(BaseModel):
    descripcion_corta: constr(min_length=1, max_length=200, strip_whitespace=True)
    descripcion_larga: Optional[constr(max_length=1000)] = None
    estado: Optional[str] = Field(default="activo", pattern="^(activo|inactivo)$")
    nombre: constr(min_length=1, max_length=255, strip_whitespace=True)
    
    @validator('nombre', 'descripcion_corta')
    def validar_campos_requeridos(cls, v):
        if not v or not v.strip():
            raise ValueError('Este campo es requerido y no puede estar vacío')
        return v.strip()
    
    @validator('estado')
    def validar_estado(cls, v):
        if v and v not in ['activo', 'inactivo']:
            raise ValueError('El estado debe ser "activo" o "inactivo"')
        return v or 'activo'

class CategoriaCreate(CategoriaBase):
    class Config:
        schema_extra = {
            "example": {
                "nombre": "Pasteles",
                "descripcion_corta": "Deliciosos pasteles artesanales",
                "descripcion_larga": "Nuestra selección de pasteles incluye opciones para todos los gustos",
                "estado": "activo"
            }
        }

class Categoria(CategoriaBase):
    id_categoria: int
    class Config:
        from_attributes = True

class ProductoBase(BaseModel):
    id_categoria: int = Field(gt=0, description="ID de la categoría")
    nombre: constr(min_length=1, max_length=255, strip_whitespace=True)
    descripcion: constr(min_length=1, max_length=2000)
    cantidad: int = Field(ge=0, description="Cantidad en inventario")
    precio: float = Field(gt=0, le=999999.99, description="Precio del producto")
    imagen_url: Optional[constr(max_length=500)] = None
    estado: Optional[str] = Field(default="activo", pattern="^(activo|inactivo)$")
    
    @validator('nombre', 'descripcion')
    def validar_campos_requeridos(cls, v):
        if not v or not v.strip():
            raise ValueError('Este campo es requerido y no puede estar vacío')
        return v.strip()
    
    @validator('precio')
    def validar_precio(cls, v):
        if v <= 0:
            raise ValueError('El precio debe ser mayor a 0')
        if v > 999999.99:
            raise ValueError('El precio no puede exceder 999,999.99')
        return round(v, 2)
    
    @validator('cantidad')
    def validar_cantidad(cls, v):
        if v < 0:
            raise ValueError('La cantidad no puede ser negativa')
        return v
    
    @validator('estado')
    def validar_estado(cls, v):
        if v and v not in ['activo', 'inactivo']:
            raise ValueError('El estado debe ser "activo" o "inactivo"')
        return v or 'activo'

class ProductoCreate(ProductoBase):
    class Config:
        schema_extra = {
            "example": {
                "id_categoria": 1,
                "nombre": "Pastel de Chocolate",
                "descripcion": "Delicioso pastel de chocolate con crema",
                "cantidad": 10,
                "precio": 25.99,
                "imagen_url": "https://ejemplo.com/pastel-chocolate.jpg",
                "estado": "activo"
            }
        }

class Producto(ProductoBase):
    id_producto: int
    categoria: Categoria
    class Config:
        from_attributes = True

class EstadoPedido(str, Enum):
    pendiente = "pendiente"
    pago_confirmado = "Pago confirmado"
    en_preparacion = "En preparación"
    en_domicilio = "En domicilio"
    listo_para_recoger = "Listo para recoger"
    entregado = "Entregado"

class MetodoPago(str, Enum):
    paypal = "PayPal"
    tarjeta = "Tarjeta"
    efectivo = "Efectivo"

class PedidoBase(BaseModel):
    id_cliente: int = Field(gt=0, description="ID del cliente")
    estado: Optional[str] = Field(default="pendiente")
    direccion_envio: constr(min_length=5, max_length=500, strip_whitespace=True)
    metodo_pago: Optional[str] = Field(default="PayPal")
    
    @validator('estado')
    def validar_estado(cls, v):
        estados_validos = ["pendiente", "Pago confirmado", "En preparación", 
                          "En domicilio", "Listo para recoger", "Entregado"]
        if v and v not in estados_validos:
            raise ValueError(f'El estado debe ser uno de: {", ".join(estados_validos)}')
        return v or "pendiente"
    
    @validator('direccion_envio')
    def validar_direccion(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError('La dirección de envío debe tener al menos 5 caracteres')
        return v.strip()
    
    @validator('metodo_pago')
    def validar_metodo_pago(cls, v):
        metodos_validos = ["PayPal", "Tarjeta", "Efectivo"]
        if v and v not in metodos_validos:
            raise ValueError(f'El método de pago debe ser uno de: {", ".join(metodos_validos)}')
        return v or "PayPal"

class PedidoCreate(PedidoBase):
    class Config:
        schema_extra = {
            "example": {
                "id_cliente": 1,
                "estado": "pendiente",
                "direccion_envio": "Calle Principal 123, Ciudad",
                "metodo_pago": "PayPal"
            }
        }

class Pedido(PedidoBase):
    id_pedido: int
    fecha_pedido: datetime
    cliente: Cliente
    class Config:
        from_attributes = True

class DetallePedidoBase(BaseModel):
    id_pedido: int = Field(gt=0, description="ID del pedido")
    id_producto: int = Field(gt=0, description="ID del producto")
    cantidad: int = Field(gt=0, le=1000, description="Cantidad del producto")
    precio_unitario: float = Field(gt=0, le=999999.99, description="Precio unitario")
    
    @validator('cantidad')
    def validar_cantidad(cls, v):
        if v <= 0:
            raise ValueError('La cantidad debe ser mayor a 0')
        if v > 1000:
            raise ValueError('La cantidad no puede exceder 1000 unidades')
        return v
    
    @validator('precio_unitario')
    def validar_precio_unitario(cls, v):
        if v <= 0:
            raise ValueError('El precio unitario debe ser mayor a 0')
        if v > 999999.99:
            raise ValueError('El precio unitario no puede exceder 999,999.99')
        return round(v, 2)

class DetallePedidoCreate(DetallePedidoBase):
    class Config:
        schema_extra = {
            "example": {
                "id_pedido": 1,
                "id_producto": 1,
                "cantidad": 2,
                "precio_unitario": 25.99
            }
        }

class DetallePedido(DetallePedidoBase):
    id_detalle: int
    subtotal: float
    pedido: Pedido
    producto: Producto
    class Config:
        from_attributes = True

class CarritoBase(BaseModel):
    id_cliente: int = Field(gt=0, description="ID del cliente")
    estado: Optional[str] = Field(default="activo", pattern="^(activo|inactivo|completado)$")
    
    @validator('estado')
    def validar_estado(cls, v):
        estados_validos = ['activo', 'inactivo', 'completado']
        if v and v not in estados_validos:
            raise ValueError(f'El estado debe ser uno de: {", ".join(estados_validos)}')
        return v or 'activo'

class CarritoCreate(CarritoBase):
    class Config:
        schema_extra = {
            "example": {
                "id_cliente": 1,
                "estado": "activo"
            }
        }

class Carrito(CarritoBase):
    id_carrito: int
    fecha_creacion: datetime
    cliente: Cliente
    class Config:
        from_attributes = True

class DetalleCarritoBase(BaseModel):
    id_carrito: int = Field(gt=0, description="ID del carrito")
    id_producto: int = Field(gt=0, description="ID del producto")
    cantidad: int = Field(gt=0, le=1000, description="Cantidad del producto")
    precio_unitario: float = Field(gt=0, le=999999.99, description="Precio unitario")
    subtotal: float = Field(ge=0, description="Subtotal calculado")
    
    @validator('cantidad')
    def validar_cantidad(cls, v):
        if v <= 0:
            raise ValueError('La cantidad debe ser mayor a 0')
        if v > 1000:
            raise ValueError('La cantidad no puede exceder 1000 unidades')
        return v
    
    @validator('precio_unitario')
    def validar_precio_unitario(cls, v):
        if v <= 0:
            raise ValueError('El precio unitario debe ser mayor a 0')
        if v > 999999.99:
            raise ValueError('El precio unitario no puede exceder 999,999.99')
        return round(v, 2)
    
    @validator('subtotal', always=True)
    def validar_subtotal(cls, v, values):
        # En Pydantic v1, values es un dict que puede no tener todos los campos
        cantidad = values.get('cantidad')
        precio_unitario = values.get('precio_unitario')
        
        if cantidad is not None and precio_unitario is not None:
            calculado = cantidad * precio_unitario
            if abs(v - calculado) > 0.01:  # Tolerancia para errores de punto flotante
                raise ValueError(f'El subtotal debe ser igual a cantidad × precio_unitario ({calculado:.2f})')
        
        if v is not None and v < 0:
            raise ValueError('El subtotal no puede ser negativo')
        
        return round(v, 2) if v is not None else v

class DetalleCarritoCreate(DetalleCarritoBase):
    class Config:
        schema_extra = {
            "example": {
                "id_carrito": 1,
                "id_producto": 1,
                "cantidad": 2,
                "precio_unitario": 25.99,
                "subtotal": 51.98
            }
        }

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
    metadatos_extra: Optional[dict] = None
    
    class Config:
        from_attributes = True