"""
Tests de integración para endpoints de productos y categorías.
"""

import pytest
from tests.conftest import get_auth_headers


class TestCategoriaEndpoints:
    """Pruebas para endpoints de categorías."""
    
    def test_crear_categoria_exitoso(self, client, token_admin_test):
        """Prueba crear categoría exitosamente."""
        response = client.post(
            "/categorias/",
            json={
                "nombre": "Ropa",
                "descripcion_corta": "Ropa y accesorios",
                "descripcion_larga": "Toda clase de ropa y accesorios",
                "estado": "activo"
            },
            headers=get_auth_headers(token_admin_test)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == "Ropa"
        assert "id_categoria" in data
    
    def test_listar_categorias(self, client, categoria_test):
        """Prueba listar categorías."""
        response = client.get("/categorias/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_productos_de_categoria(self, client, categoria_test, producto_test):
        """Prueba obtener productos de una categoría."""
        response = client.get(f"/categorias/{categoria_test.id_categoria}/productos")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


class TestProductoEndpoints:
    """Pruebas para endpoints de productos."""
    
    def test_crear_producto_exitoso(self, client, categoria_test, token_admin_test):
        """Prueba crear producto exitosamente."""
        response = client.post(
            "/productos/",
            json={
                "id_categoria": categoria_test.id_categoria,
                "nombre": "Laptop",
                "descripcion": "Laptop de alta gama",
                "cantidad": 20,
                "precio": 1299.99,
                "estado": "activo"
            },
            headers=get_auth_headers(token_admin_test)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == "Laptop"
        assert data["precio"] == 1299.99
        assert "id_producto" in data
    
    def test_crear_producto_categoria_inexistente(self, client, token_admin_test):
        """Prueba crear producto con categoría inexistente."""
        response = client.post(
            "/productos/",
            json={
                "id_categoria": 99999,
                "nombre": "Producto Test",
                "descripcion": "Test",
                "cantidad": 10,
                "precio": 99.99
            },
            headers=get_auth_headers(token_admin_test)
        )
        
        assert response.status_code == 404
        assert "no encontrada" in response.json()["detail"].lower()
    
    def test_crear_producto_precio_invalido(self, client, categoria_test, token_admin_test):
        """Prueba crear producto con precio inválido."""
        response = client.post(
            "/productos/",
            json={
                "id_categoria": categoria_test.id_categoria,
                "nombre": "Producto Test",
                "descripcion": "Test",
                "cantidad": 10,
                "precio": -10.0  # Precio negativo
            },
            headers=get_auth_headers(token_admin_test)
        )
        
        assert response.status_code == 422
    
    def test_listar_productos(self, client, producto_test):
        """Prueba listar productos."""
        response = client.get("/productos/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_actualizar_producto_exitoso(self, client, producto_test, token_admin_test):
        """Prueba actualizar producto exitosamente."""
        response = client.put(
            f"/productos/{producto_test.id_producto}",
            json={
                "id_categoria": producto_test.id_categoria,
                "nombre": "Producto Actualizado",
                "descripcion": producto_test.descripcion,
                "cantidad": producto_test.cantidad,
                "precio": 899.99,
                "estado": "activo"
            },
            headers=get_auth_headers(token_admin_test)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Producto Actualizado"
        assert data["precio"] == 899.99
    
    def test_eliminar_producto_exitoso(self, client, producto_test, token_admin_test):
        """Prueba eliminar producto exitosamente."""
        response = client.delete(
            f"/productos/{producto_test.id_producto}",
            headers=get_auth_headers(token_admin_test)
        )
        
        assert response.status_code == 200
        assert "eliminado" in response.json()["mensaje"].lower()
    
    def test_eliminar_producto_no_existe(self, client, token_admin_test):
        """Prueba eliminar producto inexistente."""
        response = client.delete(
            "/productos/99999",
            headers=get_auth_headers(token_admin_test)
        )
        
        assert response.status_code == 404

    def test_agregar_producto_identico_suma_stock(self, client, categoria_test, token_admin_test):
        """CP-015: Prueba que agregar un producto idéntico suma el stock."""
        # 1. Crear el producto inicial
        nombre_producto = "Torta de Fresa Única"
        cantidad_inicial = 10
        producto_data = {
            "id_categoria": categoria_test.id_categoria,
            "nombre": nombre_producto,
            "descripcion": "Torta de fresa para probar stock",
            "cantidad": cantidad_inicial,
            "precio": 25.00,
            "estado": "activo"
        }
        response1 = client.post(
            "/productos/",
            json=producto_data,
            headers=get_auth_headers(token_admin_test)
        )
        assert response1.status_code == 201
        assert response1.json()["cantidad"] == producto_data["cantidad"]

        # Intentar crear el mismo producto de nuevo
        response2 = client.post(
            "/productos/",
            json=producto_data,
            headers=get_auth_headers(token_admin_test)
        )
        assert response2.status_code == 201
        
        # Verificar que el stock se haya sumado
        producto_actualizado = response2.json()
        
        cantidad_total_esperada = cantidad_inicial + cantidad_inicial # The original code had cantidad_adicional, but it was removed. Assuming it should be the same as the initial quantity.
        assert producto_actualizado["cantidad"] == cantidad_total_esperada

        # 4. Verificar que no se creó un producto nuevo
        response_busqueda = client.get(f"/productos/?nombre={nombre_producto}")
        productos_encontrados = response_busqueda.json()
        assert len(productos_encontrados) == 1

