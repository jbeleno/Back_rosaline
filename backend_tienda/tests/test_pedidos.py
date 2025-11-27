"""
Tests de integración para endpoints de pedidos y clientes.
"""

import pytest
from tests.conftest import get_auth_headers


class TestClienteEndpoints:
    """Pruebas para endpoints de clientes."""
    
    def test_crear_cliente_exitoso(self, client, usuario_test, token_test):
        """Prueba crear cliente exitosamente."""
        response = client.post(
            "/clientes/",
            json={
                "id_usuario": usuario_test.id_usuario,
                "nombre": "María",
                "apellido": "González",
                "telefono": "987654321",
                "direccion": "Calle Nueva 456"
            },
            headers=get_auth_headers(token_test)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == "María"
        assert data["apellido"] == "González"
        assert "id_cliente" in data
    
    def test_crear_cliente_usuario_inexistente(self, client, token_test):
        """Prueba crear cliente con usuario inexistente."""
        response = client.post(
            "/clientes/",
            json={
                "id_usuario": 99999,
                "nombre": "Test",
                "apellido": "Cliente"
            },
            headers=get_auth_headers(token_test)
        )
        
        # Ahora devuelve 403 porque el usuario solo puede crear su propio perfil
        # o 404 si el usuario no existe en el sistema
        assert response.status_code in [403, 404]
    
    def test_listar_clientes(self, client, cliente_test, token_admin_test):
        """Prueba listar clientes."""
        response = client.get(
            "/clientes/",
            headers=get_auth_headers(token_admin_test)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_obtener_cliente_por_usuario(self, client, cliente_test, usuario_test, token_test):
        """Prueba obtener cliente por ID de usuario."""
        response = client.get(
            f"/clientes/usuario/{usuario_test.id_usuario}",
            headers=get_auth_headers(token_test)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id_cliente"] == cliente_test.id_cliente


class TestPedidoEndpoints:
    """Pruebas para endpoints de pedidos."""
    
    def test_crear_pedido_exitoso(self, client, cliente_test, token_test):
        """Prueba crear pedido exitosamente."""
        response = client.post(
            "/pedidos/",
            json={
                "id_cliente": cliente_test.id_cliente,
                "estado": "pendiente",
                "direccion_envio": "Calle Envío 789",
                "metodo_pago": "Tarjeta"
            },
            headers=get_auth_headers(token_test)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["estado"] == "pendiente"
        assert "id_pedido" in data
        assert "fecha_pedido" in data
    
    def test_crear_pedido_cliente_inexistente(self, client, token_test):
        """Prueba crear pedido con cliente inexistente."""
        response = client.post(
            "/pedidos/",
            json={
                "id_cliente": 99999,
                "direccion_envio": "Calle Test",
                "estado": "pendiente"
            },
            headers=get_auth_headers(token_test)
        )
        
        assert response.status_code == 404
    
    def test_listar_pedidos(self, client, cliente_test, token_admin_test):
        """Prueba listar pedidos."""
        response = client.get(
            "/pedidos/",
            headers=get_auth_headers(token_admin_test)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_pedidos_por_estado(self, client, cliente_test, token_test):
        """Prueba listar pedidos por estado."""
        # Crear pedido con estado específico
        client.post(
            "/pedidos/",
            json={
                "id_cliente": cliente_test.id_cliente,
                "direccion_envio": "Calle Test",
                "estado": "enviado"
            },
            headers=get_auth_headers(token_test)
        )
        
        response = client.get(
            "/pedidos/estado/enviado",
            headers=get_auth_headers(token_test)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert data[0]["estado"] == "enviado"


class TestDetallePedidoEndpoints:
    """Pruebas para endpoints de detalles de pedidos."""
    
    def test_crear_detalle_pedido_exitoso(self, client, cliente_test, producto_test, token_test):
        """Prueba crear detalle de pedido exitosamente."""
        # Crear pedido primero
        pedido_response = client.post(
            "/pedidos/",
            json={
                "id_cliente": cliente_test.id_cliente,
                "direccion_envio": "Calle Test",
                "estado": "pendiente"
            },
            headers=get_auth_headers(token_test)
        )
        pedido_id = pedido_response.json()["id_pedido"]
        
        # Crear detalle de pedido
        response = client.post(
            "/detalle_pedidos/",
            json={
                "id_pedido": pedido_id,
                "id_producto": producto_test.id_producto,
                "cantidad": 5,
                "precio_unitario": float(producto_test.precio)
            },
            headers=get_auth_headers(token_test)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["cantidad"] == 5
        assert "subtotal" in data
        assert data["subtotal"] == 5 * float(producto_test.precio)
    
    def test_crear_detalle_pedido_sin_inventario(self, client, cliente_test, categoria_test, token_test, token_admin_test):
        """Prueba crear detalle de pedido sin inventario suficiente."""
        # Crear producto con cantidad limitada (requiere admin)
        producto_response = client.post(
            "/productos/",
            json={
                "id_categoria": categoria_test.id_categoria,
                "nombre": "Producto Limitado",
                "descripcion": "Test",
                "cantidad": 3,
                "precio": 10.0
            },
            headers=get_auth_headers(token_admin_test)
        )
        producto_id = producto_response.json()["id_producto"]
        
        # Crear pedido
        pedido_response = client.post(
            "/pedidos/",
            json={
                "id_cliente": cliente_test.id_cliente,
                "direccion_envio": "Calle Test",
                "estado": "pendiente"
            },
            headers=get_auth_headers(token_test)
        )
        pedido_id = pedido_response.json()["id_pedido"]
        
        # Intentar crear detalle con cantidad mayor al inventario
        response = client.post(
            "/detalle_pedidos/",
            json={
                "id_pedido": pedido_id,
                "id_producto": producto_id,
                "cantidad": 10,  # Más de lo disponible
                "precio_unitario": 10.0
            },
            headers=get_auth_headers(token_test)
        )
        
        assert response.status_code == 400
        assert "inventario" in response.json()["detail"].lower()
    
    def test_crear_detalle_pedido_descuenta_inventario(self, client, cliente_test, producto_test, token_test):
        """Prueba que crear detalle de pedido descuenta el inventario."""
        cantidad_inicial = producto_test.cantidad
        
        # Crear pedido
        pedido_response = client.post(
            "/pedidos/",
            json={
                "id_cliente": cliente_test.id_cliente,
                "direccion_envio": "Calle Test",
                "estado": "pendiente"
            },
            headers=get_auth_headers(token_test)
        )
        pedido_id = pedido_response.json()["id_pedido"]
        
        # Crear detalle de pedido
        cantidad_pedida = 10
        client.post(
            "/detalle_pedidos/",
            json={
                "id_pedido": pedido_id,
                "id_producto": producto_test.id_producto,
                "cantidad": cantidad_pedida,
                "precio_unitario": float(producto_test.precio)
            },
            headers=get_auth_headers(token_test)
        )
        
        # Verificar que el inventario se descontó
        # Obtener todos los productos y buscar el nuestro
        productos_response = client.get("/productos/")
        assert productos_response.status_code == 200
        productos = productos_response.json()
        producto_actualizado = next((p for p in productos if p["id_producto"] == producto_test.id_producto), None)
        assert producto_actualizado is not None
        assert producto_actualizado["cantidad"] == cantidad_inicial - cantidad_pedida
    
    def test_productos_de_pedido(self, client, cliente_test, producto_test, token_test):
        """Prueba obtener productos de un pedido."""
        # Crear pedido
        pedido_response = client.post(
            "/pedidos/",
            json={
                "id_cliente": cliente_test.id_cliente,
                "direccion_envio": "Calle Test",
                "estado": "pendiente"
            },
            headers=get_auth_headers(token_test)
        )
        pedido_id = pedido_response.json()["id_pedido"]
        
        # Crear detalle de pedido
        client.post(
            "/detalle_pedidos/",
            json={
                "id_pedido": pedido_id,
                "id_producto": producto_test.id_producto,
                "cantidad": 5,
                "precio_unitario": float(producto_test.precio)
            },
            headers=get_auth_headers(token_test)
        )
        
        # Obtener productos del pedido
        response = client.get(
            f"/pedidos/{pedido_id}/productos",
            headers=get_auth_headers(token_test)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_calculo_total_pedido_con_varios_productos(self, client, cliente_test, categoria_test, token_test, token_admin_test):
        """CP-013: Verifica que el total del pedido se calcula correctamente con múltiples productos."""
        # 1. Crear dos productos distintos
        producto1_res = client.post("/productos/", headers=get_auth_headers(token_admin_test), json={
            "id_categoria": categoria_test.id_categoria, "nombre": "Producto A", "descripcion": "Desc A",
            "cantidad": 100, "precio": 10.50, "estado": "activo"
        })
        assert producto1_res.status_code == 201
        producto1 = producto1_res.json()

        producto2_res = client.post("/productos/", headers=get_auth_headers(token_admin_test), json={
            "id_categoria": categoria_test.id_categoria, "nombre": "Producto B", "descripcion": "Desc B",
            "cantidad": 100, "precio": 5.25, "estado": "activo"
        })
        assert producto2_res.status_code == 201
        producto2 = producto2_res.json()

        # 2. Crear un pedido
        pedido_res = client.post("/pedidos/", headers=get_auth_headers(token_test), json={
            "id_cliente": cliente_test.id_cliente, "estado": "pendiente",
            "direccion_envio": "Calle Falsa 123", "metodo_pago": "Tarjeta"
        })
        assert pedido_res.status_code == 201
        pedido_id = pedido_res.json()["id_pedido"]

        # 3. Añadir ambos productos al pedido
        # Item 1: 3 unidades del Producto A
        subtotal1 = 3 * producto1["precio"]
        client.post("/detalle_pedidos/", headers=get_auth_headers(token_test), json={
            "id_pedido": pedido_id, "id_producto": producto1["id_producto"],
            "cantidad": 3, "precio_unitario": producto1["precio"]
        })

        # Item 2: 2 unidades del Producto B
        subtotal2 = 2 * producto2["precio"]
        client.post("/detalle_pedidos/", headers=get_auth_headers(token_test), json={
            "id_pedido": pedido_id, "id_producto": producto2["id_producto"],
            "cantidad": 2, "precio_unitario": producto2["precio"]
        })

        # 4. Obtener el pedido y verificar el total
        response_pedido = client.get(f"/pedidos/{pedido_id}", headers=get_auth_headers(token_test))
        assert response_pedido.status_code == 200
        pedido_actualizado = response_pedido.json()

        total_esperado = subtotal1 + subtotal2
        
        # Asumiendo que el campo se llama 'total' en el modelo Pedido
        assert "total" in pedido_actualizado
        assert pedido_actualizado["total"] == pytest.approx(total_esperado, rel=1e-9)

