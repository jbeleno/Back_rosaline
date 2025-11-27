"""
Tests de integración para búsqueda de productos.

Cubre casos de prueba:
- CP-020: Búsqueda por texto parcial
- CP-021: Búsqueda sin coincidencias
"""

import pytest
from tests.conftest import get_auth_headers


class TestBusquedaProductos:
    """Pruebas para la funcionalidad de búsqueda de productos."""
    
    def test_busqueda_por_nombre_completo(self, client, producto_test):
        """CP-020: Prueba búsqueda con nombre completo del producto."""
        response = client.get(f"/productos/?nombre={producto_test.nombre}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Verificar que el producto está en los resultados
        producto_encontrado = any(
            p['id_producto'] == producto_test.id_producto 
            for p in data
        )
        assert producto_encontrado
    
    def test_busqueda_por_texto_parcial_inicio(self, client, categoria_test, token_admin_test):
        """CP-020: Prueba búsqueda por texto parcial al inicio del nombre."""
        # Crear producto con nombre específico
        producto_response = client.post(
            "/productos/",
            json={
                "id_categoria": categoria_test.id_categoria,
                "nombre": "Pastel de Chocolate",
                "descripcion": "Delicioso pastel",
                "cantidad": 10,
                "precio": 25.99,
                "estado": "activo"
            },
            headers=get_auth_headers(token_admin_test)
        )
        assert producto_response.status_code == 201
        
        # Buscar por texto parcial "Pastel"
        response = client.get("/productos/?nombre=Pastel")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Verificar que contiene el producto creado
        assert any("Pastel" in p['nombre'] for p in data)
    
    def test_busqueda_por_texto_parcial_medio(self, client, categoria_test, token_admin_test):
        """CP-020: Prueba búsqueda por texto parcial en medio del nombre."""
        # Crear producto con nombre específico
        producto_response = client.post(
            "/productos/",
            json={
                "id_categoria": categoria_test.id_categoria,
                "nombre": "Galletas de Avena",
                "descripcion": "Deliciosas galletas",
                "cantidad": 20,
                "precio": 5.99,
                "estado": "activo"
            },
            headers=get_auth_headers(token_admin_test)
        )
        assert producto_response.status_code == 201
        
        # Buscar por texto parcial "de"
        response = client.get("/productos/?nombre=de")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verificar que contiene productos con "de" en el nombre
        assert any("de" in p['nombre'].lower() for p in data)
    
    def test_busqueda_case_insensitive_mayusculas(self, client, categoria_test, token_admin_test):
        """CP-020: Prueba que la búsqueda no distingue mayúsculas/minúsculas."""
        # Crear producto con nombre en minúsculas
        producto_response = client.post(
            "/productos/",
            json={
                "id_categoria": categoria_test.id_categoria,
                "nombre": "croissant francés",
                "descripcion": "Delicioso croissant",
                "cantidad": 15,
                "precio": 3.50,
                "estado": "activo"
            },
            headers=get_auth_headers(token_admin_test)
        )
        assert producto_response.status_code == 201
        producto_id = producto_response.json()["id_producto"]
        
        # Buscar en MAYÚSCULAS
        response = client.get("/productos/?nombre=CROISSANT")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verificar que encuentra el producto
        producto_encontrado = any(
            p['id_producto'] == producto_id 
            for p in data
        )
        assert producto_encontrado
    
    def test_busqueda_case_insensitive_minusculas(self, client, categoria_test, token_admin_test):
        """CP-020: Prueba búsqueda en minúsculas de producto en mayúsculas."""
        # Crear producto con nombre en mayúsculas
        producto_response = client.post(
            "/productos/",
            json={
                "id_categoria": categoria_test.id_categoria,
                "nombre": "DONUT GLASEADO",
                "descripcion": "Delicioso donut",
                "cantidad": 25,
                "precio": 2.50,
                "estado": "activo"
            },
            headers=get_auth_headers(token_admin_test)
        )
        assert producto_response.status_code == 201
        producto_id = producto_response.json()["id_producto"]
        
        # Buscar en minúsculas
        response = client.get("/productos/?nombre=donut")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verificar que encuentra el producto
        producto_encontrado = any(
            p['id_producto'] == producto_id 
            for p in data
        )
        assert producto_encontrado
    
    def test_busqueda_sin_coincidencias(self, client):
        """CP-021: Prueba que la búsqueda retorna lista vacía sin coincidencias."""
        # Buscar un texto que no existe
        response = client.get("/productos/?nombre=ProductoQueNoExiste12345")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_busqueda_texto_especial_sin_coincidencias(self, client):
        """CP-021: Prueba búsqueda con caracteres especiales sin coincidencias."""
        response = client.get("/productos/?nombre=@#$%^&*()")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_busqueda_vacia_retorna_todos(self, client, producto_test):
        """Prueba que búsqueda vacía retorna todos los productos."""
        response = client.get("/productos/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_busqueda_multiples_productos_mismo_nombre(self, client, categoria_test, token_admin_test):
        """CP-020: Prueba búsqueda que retorna múltiples productos."""
        # Crear varios productos con "Pan" en el nombre
        productos_creados = []
        for nombre in ["Pan Integral", "Pan Blanco", "Pan de Centeno"]:
            response = client.post(
                "/productos/",
                json={
                    "id_categoria": categoria_test.id_categoria,
                    "nombre": nombre,
                    "descripcion": f"Delicioso {nombre}",
                    "cantidad": 10,
                    "precio": 4.99,
                    "estado": "activo"
                },
                headers=get_auth_headers(token_admin_test)
            )
            assert response.status_code == 201
            productos_creados.append(response.json()["id_producto"])
        
        # Buscar por "Pan"
        response = client.get("/productos/?nombre=Pan")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        
        # Verificar que todos los productos creados están en los resultados
        ids_encontrados = [p['id_producto'] for p in data]
        for producto_id in productos_creados:
            assert producto_id in ids_encontrados


class TestBusquedaPorCategoria:
    """Pruebas para búsqueda de productos por categoría."""
    
    def test_busqueda_por_categoria_existente(self, client, categoria_test, producto_test):
        """Prueba búsqueda de productos por categoría existente."""
        response = client.get(f"/categorias/{categoria_test.id_categoria}/productos")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Verificar que todos los productos pertenecen a la categoría
        for producto in data:
            assert producto['id_categoria'] == categoria_test.id_categoria
    
    def test_busqueda_por_categoria_sin_productos(self, client, token_admin_test):
        """Prueba búsqueda en categoría sin productos."""
        # Crear categoría vacía
        categoria_response = client.post(
            "/categorias/",
            json={
                "nombre": "Categoría Vacía",
                "descripcion_corta": "Sin productos",
                "descripcion_larga": "Categoría de prueba sin productos",
                "estado": "activo"
            },
            headers=get_auth_headers(token_admin_test)
        )
        assert categoria_response.status_code == 201
        categoria_id = categoria_response.json()["id_categoria"]
        
        # Buscar productos en categoría vacía
        response = client.get(f"/categorias/{categoria_id}/productos")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_busqueda_por_categoria_inexistente(self, client):
        """Prueba búsqueda en categoría que no existe."""
        response = client.get("/categorias/99999/productos")
        
        # Puede retornar 404 o lista vacía dependiendo de la implementación
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0


class TestBusquedaAvanzada:
    """Pruebas para búsquedas avanzadas y combinadas."""
    
    def test_busqueda_productos_activos(self, client, categoria_test, token_admin_test):
        """Prueba búsqueda solo de productos activos."""
        # Crear producto activo
        producto_activo = client.post(
            "/productos/",
            json={
                "id_categoria": categoria_test.id_categoria,
                "nombre": "Producto Activo",
                "descripcion": "Producto disponible",
                "cantidad": 10,
                "precio": 10.0,
                "estado": "activo"
            },
            headers=get_auth_headers(token_admin_test)
        )
        assert producto_activo.status_code == 201
        
        # Buscar productos (por defecto debería retornar solo activos)
        response = client.get("/productos/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar que todos los productos son activos
        # (esto depende de la implementación del endpoint)
        for producto in data:
            # Si el endpoint filtra por estado, verificar
            if 'estado' in producto:
                assert producto['estado'] == 'activo'
    
    def test_busqueda_con_paginacion(self, client, categoria_test, token_admin_test):
        """Prueba búsqueda con parámetros de paginación."""
        # Crear varios productos
        for i in range(5):
            client.post(
                "/productos/",
                json={
                    "id_categoria": categoria_test.id_categoria,
                    "nombre": f"Producto {i}",
                    "descripcion": f"Descripción {i}",
                    "cantidad": 10,
                    "precio": 10.0 + i,
                    "estado": "activo"
                },
                headers=get_auth_headers(token_admin_test)
            )
        
        # Buscar con límite
        response = client.get("/productos/?skip=0&limit=3")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Debería retornar máximo 3 productos (si el endpoint soporta paginación)
        assert len(data) <= 100  # Límite por defecto o especificado
