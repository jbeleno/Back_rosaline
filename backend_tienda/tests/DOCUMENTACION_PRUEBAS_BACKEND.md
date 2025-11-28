# Documentación de Pruebas – Backend Rosaline

## 1. Estructura de la Carpeta `tests`

La carpeta `tests` contiene las pruebas automatizadas del backend de la tienda en línea. Actualmente incluye los siguientes módulos principales:

- `test_auth.py` – Pruebas unitarias de autenticación y tokens.
- `test_usuarios.py` – Pruebas de integración para login y CRUD de usuarios.
- `test_productos.py` – Pruebas de integración para categorías y productos (incluye stock).
- `test_pedidos.py` – Pruebas de integración para clientes, pedidos y detalles de pedido.
- `test_carritos.py` – Pruebas de integración para carritos y detalles de carrito.
- `test_busqueda.py` – Pruebas de integración para búsqueda de productos.
- `test_notificaciones.py` – Pruebas del sistema de notificaciones (servicio de email).
- `test_validaciones.py` – Pruebas unitarias de validación con Pydantic.
- `conftest.py` – Fixtures reutilizables para clientes, usuarios, productos, tokens, etc.

El archivo `RESUMEN_PRUEBAS_AGREGADAS.md` complementa esta documentación describiendo casos de prueba específicos (CP-XXX) y cobertura global.

---

## 2. `test_auth.py` – Pruebas de Autenticación

**Objetivo:** validar la lógica de autenticación localizada en `app.auth`.

**Funcionalidades cubiertas:**

- Hash de contraseñas:
  - Generación de hash a partir de contraseñas en texto plano.
  - Verificación de que el hash es distinto al texto original.
  - Diferentes ejecuciones generan hashes distintos para la misma contraseña (salt).
- Verificación de contraseñas:
  - Acepta una contraseña correcta frente a su hash.
  - Rechaza una contraseña incorrecta.
- Tokens JWT:
  - Creación de tokens de acceso con payload que incluye `sub`, `id_usuario` y `rol`.
  - Creación de tokens con expiración personalizada (`expires_delta`).
  - Verificación de tokens válidos (retorna el payload con los datos esperados).
  - Manejo de tokens inválidos (retorna `None`).
  - Preservación de datos adicionales en el token (campos extra).

---

## 3. `test_usuarios.py` – Pruebas de Usuarios y Login

**Objetivo:** validar endpoints relacionados con autenticación de usuarios y gestión de cuentas.

**Casos de prueba (CP) cubiertos:**
- **CP-001 – Registro de nuevo usuario**
- **CP-002 – Inicio de sesión**
- **CP-007 – Validación de email en registro**

**Casos cubiertos (endpoints principales):**

- `POST /login`:
  - Login exitoso con credenciales válidas (retorna `access_token` tipo `bearer`).
  - Login con correo inexistente (retorna 401 y mensaje de error adecuado).
  - Login con contraseña incorrecta (retorna 401 con mensaje de error).
  - Login con datos incompletos (falta contraseña) – valida errores 422.

- `POST /usuarios/`:
  - Creación exitosa de usuario (correo, contraseña, rol).
  - Verificación de que la contraseña no se retorna en la respuesta.
  - Intento de creación con correo duplicado (retorna 400 con mensaje "Correo ya registrado").
  - Creación con datos inválidos (email sin `@`, contraseña débil) – verifica respuesta 200/422 según lógica.

- `PUT /usuarios/{id_usuario}`:
  - Actualización exitosa de datos del usuario (correo, contraseña, rol) con permisos de admin.
  - Intento de actualizar usuario inexistente (retorna 404).

- `DELETE /usuarios/{id_usuario}`:
  - Eliminación exitosa de usuario existente.
  - Intento de eliminar usuario inexistente (404).

- `GET /usuarios/me`:
  - Obtención de datos del usuario autenticado con token válido.
  - Acceso sin token (retorna 401).

---

## 4. `test_productos.py` – Pruebas de Productos y Categorías

**Objetivo:** validar endpoints de gestión de categorías y productos, incluyendo reglas de negocio sobre stock.

**Casos de prueba (CP) cubiertos:**
- **CP-014 – Eliminación lógica de productos**
- **CP-015 – Suma de stock al agregar producto**

**Casos cubiertos (ejemplos):**

- Categorías (`/categorias/`):
  - Creación exitosa de categoría (nombre, descripciones, estado).
  - Listado de categorías existentes (estructura de lista, no vacía).
  - Obtención de productos asociados a una categoría específica.

- Productos (`/productos/`):
  - Creación exitosa de producto asociado a una categoría válida.
  - Creación de producto con categoría inexistente (retorna 404 con mensaje de "no encontrada").
  - Creación con precio inválido (negativo) – retorna 422.
  - Listado general de productos (lista no vacía).
  - Actualización de producto (nombre, precio, estado) y verificación de cambios.
  - Eliminación lógica/física de producto exitosamente.
  - Intento de eliminar producto inexistente (404).

- Regla de negocio de stock (CP-015):
  - Al intentar crear nuevamente un producto idéntico (misma categoría, nombre, descripción, etc.),
    en lugar de crear un registro nuevo se suma el stock sobre el producto existente.
  - Validación de que solo existe un producto con ese nombre y que la cantidad es la suma esperada.

---

## 5. `test_pedidos.py` – Pruebas de Clientes y Pedidos

**Objetivo:** validar el flujo de creación y consulta de clientes y pedidos, así como el cálculo de totales.

**Casos de prueba (CP) cubiertos:**
- **CP-013 – Cálculo de total del pedido**

**Casos cubiertos (ejemplos):**

- Clientes (`/clientes/`):
  - Creación exitosa de cliente a partir de un usuario existente.
  - Manejo de usuario inexistente o no autorizado (403/404).
  - Listado de clientes (lista con al menos un elemento).
  - Obtención de cliente a partir de `id_usuario`.

- Pedidos (`/pedidos/`):
  - Creación exitosa de pedido (estado, dirección de envío, método de pago).
  - Creación de pedido con cliente inexistente (403/404 según lógica).
  - Listado general de pedidos.
  - Listado filtrado de pedidos por estado.

- Detalles de pedido (`/detalle_pedidos/`):
  - Asociación de productos a un pedido (cantidad, precio unitario).
  - Verificación del descuento de inventario de los productos al crear detalles.
  - Obtención de productos asociados a un pedido (`GET /pedidos/{id_pedido}/productos`).

- Cálculo de total del pedido (CP-013):
  - Creación de un pedido con múltiples productos y distintas cantidades.
  - Cálculo del subtotal por ítem y suma final.
  - Verificación de que el campo `total` del pedido coincide con la suma esperada.

---

## 6. `test_carritos.py` – Pruebas de Carritos y Detalles

**Objetivo:** validar la lógica de carritos de compra y sus detalles (productos en el carrito).

**Casos de prueba (CP) cubiertos:**
- **CP-004 – Añadir producto al carrito**
- **CP-016 – Agregar producto repetido al carrito**
- **CP-017 – Eliminar producto del carrito**

**Casos cubiertos (ejemplos):**

- Carritos (`/carritos/`):
  - Creación exitosa de carrito asociado a un cliente (estado inicial "activo").
  - Intento de creación de carrito con cliente inexistente (403/404).
  - Listado general de carritos.
  - Obtención de carritos asociados a un cliente específico (`/clientes/{id_cliente}/carritos`).
  - Validación de restricciones cuando el usuario autenticado no tiene perfil de cliente
    (CP-004: error esperado 403/404/422 según la validación del `id_cliente`).

- Detalles de carrito (`/detalle_carrito/` y `/carritos/{id}/productos`):
  - Creación exitosa de detalle de carrito (cantidad, precio unitario, subtotal correcto).
  - Manejo de combinaciones inválidas (por ejemplo, carritos o productos inexistentes).
  - Listado de productos de un carrito (estructura de lista, campos esperados).
  - Eliminación de un detalle del carrito y verificación del resultado.

- Producto repetido en carrito (CP-016):
  - Cuando se agrega un producto que ya existe en el carrito:
    - No se crea una nueva línea independiente.
    - Se actualiza la cantidad del ítem existente.
    - Se actualiza el subtotal acorde a la nueva cantidad.

---

## 7. `test_busqueda.py` – Pruebas de Búsqueda de Productos

**Objetivo:** validar la búsqueda de productos por nombre, texto parcial y categoría.

**Casos de prueba (CP) cubiertos:**
- **CP-020 – Búsqueda por texto parcial**
- **CP-021 – Búsqueda sin coincidencias**

**Casos cubiertos:**

- CP-020 – Búsqueda por texto parcial:
  - Búsqueda por nombre completo del producto.
  - Búsqueda por texto parcial al inicio del nombre.
  - Búsqueda por texto parcial en medio del nombre.
  - Búsqueda case-insensitive (mayúsculas/minúsculas).

- CP-021 – Búsqueda sin coincidencias:
  - Búsqueda con texto que no existe.
  - Búsqueda con caracteres especiales.
  - Verificación de que se retorna lista vacía cuando no hay coincidencias.

- Búsqueda por categoría:
  - Obtención de productos de una categoría existente.
  - Categoría sin productos (retorna lista vacía).
  - Búsqueda en categoría inexistente (manejo de 200 vacía o 404, según implementación).

- Búsqueda avanzada:
  - Filtro de productos activos.
  - Búsqueda con parámetros de paginación (`skip`, `limit`).

---

## 8. `test_notificaciones.py` – Pruebas de Sistema de Notificaciones

**Objetivo:** validar que se dispare correctamente el envío de correo de confirmación tras el registro.

**Casos de prueba (CP) cubiertos:**
- **CP-019 – Generación de email de confirmación**

**Casos cubiertos (CP-019):**

- Uso de `monkeypatch` para reemplazar el servicio real de email por un mock.
- Registro de un nuevo usuario vía `POST /usuarios/`.
- Verificación de que se llama exactamente una vez a `enviar_email_confirmacion`.
- Validación de argumentos del mock:
  - Contiene el `destinatario` correcto (correo del nuevo usuario).
  - Incluye un `pin` de tipo `str` y longitud mínima esperada.

---

## 9. `test_validaciones.py` – Pruebas Unitarias de Validación (Pydantic)

**Objetivo:** validar las reglas de negocio a nivel de esquemas Pydantic definidos en `app.schemas`.

**Casos de prueba (CP) cubiertos:**
- **CP-008 – Suma de productos en el carrito**
- **CP-011 – Validación de email en registro (función)**
- **CP-012 – Validación de contraseña mínima**

**Esquemas cubiertos:**

- `UsuarioCreate` y `UsuarioUpdate`.
- `ProductoCreate`.
- `ClienteCreate`.
- `DetalleCarritoCreate`.

**Casos principales:**

- CP-011 – Validación de email en registro:
  - Emails con formato inválido (sin `@`, sin dominio, vacíos) son rechazados.
  - Emails válidos son aceptados y normalizados en el modelo.

- CP-012 – Validación de contraseña mínima:
  - Contraseñas de menos de 8 caracteres (4 y 7) son rechazadas.
  - Contraseñas de exactamente 8 caracteres son aceptadas.
  - Contraseñas de más de 8 caracteres son aceptadas.
  - Contraseñas vacías son rechazadas.

- Validaciones de `ClienteCreate`:
  - Campos obligatorios (`nombre`, `apellido`, `telefono`, `direccion`).
  - Rechazo de nombres/apellidos vacíos.
  - Rechazo de teléfonos con formato inválido (letras, formatos no permitidos).
  - Aceptación de teléfonos válidos (incluyendo prefijo internacional).

- CP-008 – Suma y validación de subtotales en `DetalleCarritoCreate`:
  - Acepta subtotales correctos según `cantidad * precio_unitario`.
  - Rechaza subtotales inconsistentes.
  - Casos con múltiples productos sumando subtotales.
  - Manejo de cantidades cero o negativas (rechazadas).

---

## 10. `conftest.py` – Fixtures Compartidas

**Objetivo:** centralizar la creación de datos y clientes de prueba.

**Responsabilidades principales:**

- Configuración de la base de datos de pruebas (generalmente SQLite en memoria).
- Creación de una instancia de `TestClient` para la API FastAPI.
- Fixtures para:
  - Usuarios (cliente, admin, etc.).
  - Clientes asociados a usuarios.
  - Categorías y productos base.
  - Tokens de autenticación (`token_test`, `token_admin_test`, `token_sin_perfil_test`).
- Helpers como `get_auth_headers(token)` para construir headers de autorización.

Estas fixtures permiten que las pruebas de todos los módulos sean más legibles, manteniendo el patrón Arrange-Act-Assert y evitando duplicación de código.

---

## 11. Cómo Ejecutar las Pruebas

Para ejecutar todas las pruebas desde la carpeta `backend_tienda`:

```bash
pytest -v
```

Para ejecutar un módulo de pruebas específico:

```bash
# Autenticación
pytest tests/test_auth.py -v

# Usuarios
pytest tests/test_usuarios.py -v

# Productos y categorías
pytest tests/test_productos.py -v

# Clientes y pedidos
pytest tests/test_pedidos.py -v

# Carritos
pytest tests/test_carritos.py -v

# Búsqueda
pytest tests/test_busqueda.py -v

# Notificaciones (email)
pytest tests/test_notificaciones.py -v

# Validaciones con Pydantic
pytest tests/test_validaciones.py -v
```

Para ejecutar con reporte de cobertura (si está configurado en `pytest.ini`):

```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

---

## 12. Resumen General

- La suite de pruebas cubre:
  - Autenticación y tokens JWT.
  - Registro, login y gestión de usuarios.
  - Gestión de categorías y productos, incluyendo reglas de stock.
  - Flujos de clientes, carritos, pedidos y sus detalles.
  - Búsquedas avanzadas de productos (texto parcial, categoría, estado, paginación).
  - Sistema de notificaciones por email (a nivel de integración con el servicio).
  - Validaciones de negocio a nivel de modelos Pydantic.
- Se aplican buenas prácticas de pruebas: uso de fixtures, separación de responsabilidades
  por archivo, y validación tanto de códigos de estado como del cuerpo de la respuesta.

---

### Estado de los casos de prueba (CP)

- **CP-001 – Registro de nuevo usuario:** cubierto en `test_usuarios.py`.
- **CP-002 – Inicio de sesión:** cubierto en `test_usuarios.py`.
- **CP-007 – Validación de email en registro (endpoint):** cubierto en `test_usuarios.py`.
- **CP-008 – Suma de productos en el carrito (validación de subtotal):** cubierto en `test_validaciones.py`.
- **CP-011 – Validación de email en registro (función/esquema):** cubierto en `test_validaciones.py`.
- **CP-012 – Validación de contraseña mínima:** cubierto en `test_validaciones.py`.
- **CP-013 – Cálculo de total del pedido:** cubierto en `test_pedidos.py`.
- **CP-014 – Eliminación lógica de productos:** cubierto en `test_productos.py` (eliminación de productos).
- **CP-015 – Suma de stock al agregar producto:** cubierto en `test_productos.py`.
- **CP-016 – Agregar producto repetido al carrito:** cubierto en `test_carritos.py`.
- **CP-017 – Eliminar producto del carrito:** cubierto en `test_carritos.py`.
- **CP-018 – Aplicar descuento porcentual:** actualmente **sin pruebas automatizadas** en esta suite.
- **CP-019 – Generación de email de confirmación:** cubierto en `test_notificaciones.py`.
- **CP-020 – Búsqueda por texto parcial:** cubierto en `test_busqueda.py`.
- **CP-021 – Búsqueda sin coincidencias:** cubierto en `test_busqueda.py`.
