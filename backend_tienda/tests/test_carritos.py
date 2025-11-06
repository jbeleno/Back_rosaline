"""
Tests de integración para endpoints de carritos.
"""

import pytest
from tests.conftest import get_auth_headers


class TestCarritoEndpoints:
    """Pruebas para endpoints de carritos."""
    
    def test_crear_carrito_exitoso(self, client, cliente_test, token_test):
        """Prueba crear carrito exitosamente."""
        response = client.post(
            "/carritos/",
            json={
                "id_cliente": cliente_test.id_cliente,
                "estado": "activo"
            },
            headers=get_auth_headers(token_test)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "activo"
        assert "id_carrito" in data
        assert "fecha_creacion" in data
    
    def test_crear_carrito_cliente_inexistente(self, client, token_test):
        """Prueba crear carrito con cliente inexistente."""
        response = client.post(
            "/carritos/",
            json={
                "id_cliente": 99999,
                "estado": "activo"
            },
            headers=get_auth_headers(token_test)
        )
        
        assert response.status_code == 404
    
    def test_listar_carritos(self, client, cliente_test, token_admin_test):
        """Prueba listar carritos."""
        response = client.get(
            "/carritos/",
            headers=get_auth_headers(token_admin_test)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_carritos_de_cliente(self, client, cliente_test, token_test):
        """Prueba obtener carritos de un cliente."""
        # Crear carrito
        client.post(
            "/carritos/",
            json={
                "id_cliente": cliente_test.id_cliente,
                "estado": "activo"
            },
            headers=get_auth_headers(token_test)
        )
        
        response = client.get(
            f"/clientes/{cliente_test.id_cliente}/carritos",
            headers=get_auth_headers(token_test)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestDetalleCarritoEndpoints:
    """Pruebas para endpoints de detalles de carritos."""
    
    def test_crear_detalle_carrito_exitoso(self, client, cliente_test, producto_test, token_test):
        """Prueba crear detalle de carrito exitosamente."""
        # Crear carrito primero
        carrito_response = client.post(
            "/carritos/",
            json={
                "id_cliente": cliente_test.id_cliente,
                "estado": "activo"
            },
            headers=get_auth_headers(token_test)
        )
        carrito_id = carrito_response.json()["id_carrito"]
        
        # Crear detalle de carrito
        cantidad = 3
        precio_unitario = float(producto_test.precio)
        subtotal = cantidad * precio_unitario
        
        response = client.post(
            "/detalle_carrito/",
            json={
                "id_carrito": carrito_id,
                "id_producto": producto_test.id_producto,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "subtotal": subtotal
            },
            headers=get_auth_headers(token_test)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["cantidad"] == cantidad
        # Usar pytest.approx para comparar números de punto flotante
        import pytest
        assert data["subtotal"] == pytest.approx(subtotal, rel=1e-9)
    
    def test_crear_detalle_carrito_sin_inventario(self, client, cliente_test, categoria_test, token_test, token_admin_test):
        """Prueba crear detalle de carrito sin inventario suficiente."""
        # Crear producto con cantidad limitada (requiere admin)
        producto_response = client.post(
            "/productos/",
            json={
                "id_categoria": categoria_test.id_categoria,
                "nombre": "Producto Limitado",
                "descripcion": "Test",
                "cantidad": 2,
                "precio": 10.0
            },
            headers=get_auth_headers(token_admin_test)
        )
        producto_id = producto_response.json()["id_producto"]
        
        # Crear carrito
        carrito_response = client.post(
            "/carritos/",
            json={
                "id_cliente": cliente_test.id_cliente,
                "estado": "activo"
            },
            headers=get_auth_headers(token_test)
        )
        carrito_id = carrito_response.json()["id_carrito"]
        
        # Intentar agregar producto con cantidad mayor al inventario
        response = client.post(
            "/detalle_carrito/",
            json={
                "id_carrito": carrito_id,
                "id_producto": producto_id,
                "cantidad": 10,  # Más de lo disponible
                "precio_unitario": 10.0,
                "subtotal": 100.0
            },
            headers=get_auth_headers(token_test)
        )
        
        assert response.status_code == 400
        assert "inventario" in response.json()["detail"].lower()
    
    def test_productos_de_carrito(self, client, cliente_test, producto_test, token_test):
        """Prueba obtener productos de un carrito."""
        # Crear carrito
        carrito_response = client.post(
            "/carritos/",
            json={
                "id_cliente": cliente_test.id_cliente,
                "estado": "activo"
            },
            headers=get_auth_headers(token_test)
        )
        carrito_id = carrito_response.json()["id_carrito"]
        
        # Crear detalle de carrito
        cantidad = 2
        precio_unitario = float(producto_test.precio)
        subtotal = cantidad * precio_unitario
        
        client.post(
            "/detalle_carrito/",
            json={
                "id_carrito": carrito_id,
                "id_producto": producto_test.id_producto,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "subtotal": subtotal
            },
            headers=get_auth_headers(token_test)
        )
        
        # Obtener productos del carrito
        response = client.get(
            f"/carritos/{carrito_id}/productos",
            headers=get_auth_headers(token_test)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_eliminar_detalle_carrito_exitoso(self, client, cliente_test, producto_test, token_test):
        """Prueba eliminar detalle de carrito exitosamente."""
        # Crear carrito
        carrito_response = client.post(
            "/carritos/",
            json={
                "id_cliente": cliente_test.id_cliente,
                "estado": "activo"
            },
            headers=get_auth_headers(token_test)
        )
        carrito_id = carrito_response.json()["id_carrito"]
        
        # Crear detalle de carrito
        detalle_response = client.post(
            "/detalle_carrito/",
            json={
                "id_carrito": carrito_id,
                "id_producto": producto_test.id_producto,
                "cantidad": 2,
                "precio_unitario": float(producto_test.precio),
                "subtotal": 2 * float(producto_test.precio)
            },
            headers=get_auth_headers(token_test)
        )
        detalle_id = detalle_response.json()["id_detalle_carrito"]
        
        # Eliminar detalle de carrito
        response = client.delete(
            f"/detalle_carrito/{detalle_id}",
            headers=get_auth_headers(token_test)
        )
        
        assert response.status_code == 200
        # El endpoint puede devolver el objeto o un mensaje
        response_data = response.json()
        assert "mensaje" in response_data or "id_detalle_carrito" in response_data

