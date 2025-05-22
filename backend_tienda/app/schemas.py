from pydantic import BaseModel
# Name: pydantic (BaseModel)
# Nombre: pydantic (BaseModel)
# Description: Provides base class for data validation and serialization using Pydantic.
# Descripción: Proporciona la clase base para validación y serialización de datos usando Pydantic.
from typing import Optional
# Name: typing (Optional)
# Nombre: typing (Optional)
# Description: Allows for optional (nullable) type hints in data models.
# Descripción: Permite anotaciones de tipo opcionales (nulos) en los modelos de datos.
from datetime import datetime
# Name: datetime (datetime)
# Nombre: datetime (datetime)
# Description: Provides date and time manipulation utilities.
# Descripción: Proporciona utilidades para manipulación de fechas y horas.

# Name: Pydantic Schemas
# Nombre: Esquemas de Pydantic
# Description: Data validation and serialization schemas for API requests and responses.
# Descripción: Esquemas de validación y serialización de datos para solicitudes y respuestas de la API.

class UsuarioBase(BaseModel):
    # Name: User Base Schema
    # Nombre: Esquema Base de Usuario
    # Description: Base schema for user data used in API.
    # Descripción: Esquema base para los datos de usuario usados en la API.
    correo: str
    rol: Optional[str] = "cliente"

class UsuarioCreate(UsuarioBase):
    # Name: User Create Schema
    # Nombre: Esquema de Creación de Usuario
    # Description: Schema for creating a new user.
    # Descripción: Esquema para la creación de un nuevo usuario.
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
