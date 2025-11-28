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
        
        assert response.status_code == 201
        data = response.json()
        assert data["estado"] == "activo"
        assert "id_carrito" in data
        assert "fecha_creacion" in data
    
    def test_crear_carrito_cliente_inexistente(self, client, token_test):
        """Prueba crear carrito con cliente inexistente."""
        response = client.post(
            "/carritos/",
            json={"id_cliente": 99999, "estado": "activo"},
            headers=get_auth_headers(token_test)
        )
        # La lógica de negocio puede devolver 403 (no autorizado para ese cliente) o 404
        assert response.status_code in [403, 404]
    
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

    def test_crear_carrito_falla_si_no_hay_perfil_cliente(self, client, token_sin_perfil_test):
        """CP-004: Verifica que no se puede crear un carrito si el usuario no tiene perfil de cliente."""
        # Se asume que la lógica de negocio requiere un `id_cliente` que se obtiene
        # a partir del usuario autenticado. Un usuario sin perfil no tendrá cliente asociado.
        # El endpoint podría fallar por varias razones:
        # 1. Espera un `id_cliente` en el payload y no lo puede obtener.
        # 2. Intenta buscar un cliente a partir del token y no lo encuentra (404).
        # 3. Considera la acción prohibida si no hay perfil (403).
        
        # Simula una llamada que un frontend haría sin tener un `id_cliente`
        response = client.post(
            "/carritos/",
            json={"estado": "activo"}, # No se envía id_cliente
            headers=get_auth_headers(token_sin_perfil_test)
        )
        
        # Esperamos un error, que podría ser 403 (prohibido) o 404 (cliente no encontrado)
        # o 422 si el id_cliente es requerido explícitamente en el schema.
        assert response.status_code in [403, 404, 422]


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
        
        assert response.status_code == 201
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

    def test_agregar_producto_repetido_actualiza_cantidad(self, client, cliente_test, producto_test, token_test):
        """CP-016: Verifica que agregar un producto existente actualiza la cantidad."""
        # 1. Crear un carrito
        carrito_response = client.post(
            "/carritos/",
            json={"id_cliente": cliente_test.id_cliente, "estado": "activo"},
            headers=get_auth_headers(token_test)
        )
        assert carrito_response.status_code == 201
        carrito_id = carrito_response.json()["id_carrito"]

        # 2. Agregar el producto por primera vez
        cantidad_inicial = 2
        precio_unitario = float(producto_test.precio)
        response1 = client.post(
            "/detalle_carrito/",
            json={
                "id_carrito": carrito_id,
                "id_producto": producto_test.id_producto,
                "cantidad": cantidad_inicial,
                "precio_unitario": precio_unitario,
                "subtotal": cantidad_inicial * precio_unitario
            },
            headers=get_auth_headers(token_test)
        )
        assert response1.status_code == 201

        # 3. Agregar el MISMO producto por segunda vez
        cantidad_adicional = 3
        response2 = client.post(
            "/detalle_carrito/",
            json={
                "id_carrito": carrito_id,
                "id_producto": producto_test.id_producto,
                "cantidad": cantidad_adicional,
                "precio_unitario": precio_unitario,
                "subtotal": cantidad_adicional * precio_unitario
            },
            headers=get_auth_headers(token_test)
        )
        assert response2.status_code == 201

        # 4. Verificar que la cantidad se ha actualizado y no hay un nuevo item
        response_items = client.get(
            f"/carritos/{carrito_id}/productos",
            headers=get_auth_headers(token_test)
        )
        assert response_items.status_code == 200
        items = response_items.json()

        # Debe haber solo un item en el carrito para este producto
        assert len(items) == 1
        
        item_carrito = items[0]
        cantidad_total_esperada = cantidad_inicial + cantidad_adicional
        subtotal_total_esperado = cantidad_total_esperada * precio_unitario

        assert item_carrito["cantidad"] == cantidad_total_esperada
        assert item_carrito["subtotal"] == pytest.approx(subtotal_total_esperado, rel=1e-9)

