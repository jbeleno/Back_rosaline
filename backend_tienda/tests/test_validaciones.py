"""
Tests unitarios para validaciones de esquemas Pydantic.

Cubre casos de prueba:
- CP-011: Validación de email en registro
- CP-012: Validación de contraseña mínima
"""

import pytest
from pydantic import ValidationError
from app.schemas import (
    UsuarioCreate,
    UsuarioUpdate,
    ProductoCreate,
    ClienteCreate,
    DetalleCarritoCreate,
)


class TestValidacionUsuario:
    """Pruebas de validación para el esquema de Usuario."""
    
    def test_validacion_email_formato_invalido(self):
        """CP-011: Prueba que la validación detecta emails con formato inválido."""
        with pytest.raises(ValidationError) as exc_info:
            UsuarioCreate(
                correo="email_sin_arroba",
                contraseña="password123",
                rol="cliente"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('correo',) for error in errors)
        assert any('email' in str(error).lower() for error in errors)
    
    def test_validacion_email_vacio(self):
        """CP-011: Prueba que la validación rechaza emails vacíos."""
        with pytest.raises(ValidationError) as exc_info:
            UsuarioCreate(
                correo="",
                contraseña="password123",
                rol="cliente"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('correo',) for error in errors)
    
    def test_validacion_email_sin_dominio(self):
        """CP-011: Prueba que la validación rechaza emails sin dominio."""
        with pytest.raises(ValidationError) as exc_info:
            UsuarioCreate(
                correo="usuario@",
                contraseña="password123",
                rol="cliente"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('correo',) for error in errors)
    
    def test_validacion_email_valido(self):
        """CP-011: Prueba que emails válidos son aceptados."""
        usuario = UsuarioCreate(
            correo="usuario@ejemplo.com",
            contraseña="password123",
            rol="cliente"
        )
        assert usuario.correo == "usuario@ejemplo.com"
    
    def test_validacion_contraseña_menor_8_caracteres(self):
        """CP-012: Prueba que la validación rechaza contraseñas menores a 8 caracteres."""
        with pytest.raises(ValidationError) as exc_info:
            UsuarioCreate(
                correo="test@ejemplo.com",
                contraseña="pass",  # Solo 4 caracteres
                rol="cliente"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('contraseña',) for error in errors)
        assert any('8' in str(error) for error in errors)
    
    def test_validacion_contraseña_7_caracteres(self):
        """CP-012: Prueba que contraseñas de 7 caracteres son rechazadas."""
        with pytest.raises(ValidationError) as exc_info:
            UsuarioCreate(
                correo="test@ejemplo.com",
                contraseña="pass123",  # 7 caracteres
                rol="cliente"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('contraseña',) for error in errors)
    
    def test_validacion_contraseña_exactamente_8_caracteres(self):
        """CP-012: Prueba que contraseñas de exactamente 8 caracteres son aceptadas."""
        usuario = UsuarioCreate(
            correo="test@ejemplo.com",
            contraseña="pass1234",  # Exactamente 8 caracteres
            rol="cliente"
        )
        assert usuario.contraseña == "pass1234"
    
    def test_validacion_contraseña_mas_8_caracteres(self):
        """CP-012: Prueba que contraseñas mayores a 8 caracteres son aceptadas."""
        usuario = UsuarioCreate(
            correo="test@ejemplo.com",
            contraseña="password123456",
            rol="cliente"
        )
        assert usuario.contraseña == "password123456"
    
    def test_validacion_contraseña_vacia(self):
        """CP-012: Prueba que contraseñas vacías son rechazadas."""
        with pytest.raises(ValidationError) as exc_info:
            UsuarioCreate(
                correo="test@ejemplo.com",
                contraseña="",
                rol="cliente"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('contraseña',) for error in errors)
    
    def test_validacion_rol_invalido(self):
        """Prueba que roles inválidos son rechazados."""
        with pytest.raises(ValidationError) as exc_info:
            UsuarioCreate(
                correo="test@ejemplo.com",
                contraseña="password123",
                rol="rol_invalido"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('rol',) for error in errors)
    
    def test_validacion_rol_valido(self):
        """Prueba que roles válidos son aceptados."""
        for rol in ['cliente', 'admin', 'super_admin']:
            usuario = UsuarioCreate(
                correo="test@ejemplo.com",
                contraseña="password123",
                rol=rol
            )
            assert usuario.rol == rol


class TestValidacionProducto:
    """Pruebas de validación para el esquema de Producto."""
    
    def test_validacion_precio_negativo(self):
        """Prueba que precios negativos son rechazados."""
        with pytest.raises(ValidationError) as exc_info:
            ProductoCreate(
                id_categoria=1,
                nombre="Producto Test",
                descripcion="Descripción del producto",
                cantidad=10,
                precio=-10.0,
                estado="activo"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('precio',) for error in errors)
    
    def test_validacion_precio_cero(self):
        """Prueba que precio cero es rechazado."""
        with pytest.raises(ValidationError) as exc_info:
            ProductoCreate(
                id_categoria=1,
                nombre="Producto Test",
                descripcion="Descripción del producto",
                cantidad=10,
                precio=0.0,
                estado="activo"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('precio',) for error in errors)
    
    def test_validacion_precio_valido(self):
        """Prueba que precios válidos son aceptados."""
        producto = ProductoCreate(
            id_categoria=1,
            nombre="Producto Test",
            descripcion="Descripción del producto",
            cantidad=10,
            precio=99.99,
            estado="activo"
        )
        assert producto.precio == 99.99
    
    def test_validacion_cantidad_negativa(self):
        """Prueba que cantidades negativas son rechazadas."""
        with pytest.raises(ValidationError) as exc_info:
            ProductoCreate(
                id_categoria=1,
                nombre="Producto Test",
                descripcion="Descripción del producto",
                cantidad=-5,
                precio=10.0,
                estado="activo"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('cantidad',) for error in errors)
    
    def test_validacion_cantidad_cero(self):
        """Prueba que cantidad cero es aceptada (sin stock)."""
        producto = ProductoCreate(
            id_categoria=1,
            nombre="Producto Test",
            descripcion="Descripción del producto",
            cantidad=0,
            precio=10.0,
            estado="activo"
        )
        assert producto.cantidad == 0
    
    def test_validacion_nombre_vacio(self):
        """Prueba que nombres vacíos son rechazados."""
        with pytest.raises(ValidationError) as exc_info:
            ProductoCreate(
                id_categoria=1,
                nombre="",
                descripcion="Descripción del producto",
                cantidad=10,
                precio=10.0,
                estado="activo"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('nombre',) for error in errors)


class TestValidacionCliente:
    """Pruebas de validación para el esquema de Cliente."""
    
    def test_validacion_nombre_vacio(self):
        """Prueba que nombres vacíos son rechazados."""
        with pytest.raises(ValidationError) as exc_info:
            ClienteCreate(
                id_usuario=1,
                nombre="",
                apellido="Pérez",
                telefono="123456789",
                direccion="Calle Test 123"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('nombre',) for error in errors)
    
    def test_validacion_apellido_vacio(self):
        """Prueba que apellidos vacíos son rechazados."""
        with pytest.raises(ValidationError) as exc_info:
            ClienteCreate(
                id_usuario=1,
                nombre="Juan",
                apellido="",
                telefono="123456789",
                direccion="Calle Test 123"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('apellido',) for error in errors)
    
    def test_validacion_telefono_formato_invalido(self):
        """Prueba que teléfonos con formato inválido son rechazados."""
        with pytest.raises(ValidationError) as exc_info:
            ClienteCreate(
                id_usuario=1,
                nombre="Juan",
                apellido="Pérez",
                telefono="abc123",  # Letras no permitidas
                direccion="Calle Test 123"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('telefono',) for error in errors)
    
    def test_validacion_telefono_valido(self):
        """Prueba que teléfonos válidos son aceptados."""
        cliente = ClienteCreate(
            id_usuario=1,
            nombre="Juan",
            apellido="Pérez",
            telefono="+1234567890",
            direccion="Calle Test 123"
        )
        assert cliente.telefono == "+1234567890"


class TestValidacionDetalleCarrito:
    """Pruebas de validación para el esquema de DetalleCarrito."""
    
    def test_validacion_subtotal_correcto(self):
        """CP-008: Prueba que el subtotal se calcula correctamente."""
        detalle = DetalleCarritoCreate(
            id_carrito=1,
            id_producto=1,
            cantidad=3,
            precio_unitario=10.0,
            subtotal=30.0
        )
        assert detalle.subtotal == 30.0
    
    def test_validacion_subtotal_incorrecto(self):
        """CP-008: Prueba que subtotales incorrectos son rechazados."""
        with pytest.raises(ValidationError) as exc_info:
            DetalleCarritoCreate(
                id_carrito=1,
                id_producto=1,
                cantidad=3,
                precio_unitario=10.0,
                subtotal=25.0  # Incorrecto, debería ser 30.0
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('subtotal',) for error in errors)
    
    def test_validacion_subtotal_dos_productos(self):
        """CP-008: Prueba el cálculo de subtotal con múltiples productos."""
        # Producto 1
        detalle1 = DetalleCarritoCreate(
            id_carrito=1,
            id_producto=1,
            cantidad=2,
            precio_unitario=15.50,
            subtotal=31.0
        )
        
        # Producto 2
        detalle2 = DetalleCarritoCreate(
            id_carrito=1,
            id_producto=2,
            cantidad=3,
            precio_unitario=20.0,
            subtotal=60.0
        )
        
        total = detalle1.subtotal + detalle2.subtotal
        assert total == 91.0
    
    def test_validacion_cantidad_cero(self):
        """Prueba que cantidad cero es rechazada."""
        with pytest.raises(ValidationError) as exc_info:
            DetalleCarritoCreate(
                id_carrito=1,
                id_producto=1,
                cantidad=0,
                precio_unitario=10.0,
                subtotal=0.0
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('cantidad',) for error in errors)
    
    def test_validacion_cantidad_negativa(self):
        """Prueba que cantidades negativas son rechazadas."""
        with pytest.raises(ValidationError) as exc_info:
            DetalleCarritoCreate(
                id_carrito=1,
                id_producto=1,
                cantidad=-5,
                precio_unitario=10.0,
                subtotal=-50.0
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('cantidad',) for error in errors)
