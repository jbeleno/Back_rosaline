# Contexto de Pruebas Backend (Rosaline Bakery)

Este documento sirve como guía de contexto para las pruebas del backend, con el fin de eliminar pruebas orientadas al frontend y definir una cobertura adecuada para el backend.

## Casos de Prueba Backend

| Id      | Caso de Prueba                                | Descripción                                                                                                                        | Fecha       | Área Funcional / Sub proceso   |
|---------|-----------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|-------------|--------------------------------|
| CP-001  | Registro de nuevo usuario                     | Verificar que el usuario puede registrarse exitosamente con un correo y contraseña válidos y que recibe un PIN de confirmación por email. | 11/8/2025   | Backend – Autenticación        |
| CP-002  | Inicio de sesión                              | Verificar que un usuario confirmado puede iniciar sesión y recibe un token JWT.                                                     | 11/8/2025   | Backend – Autenticación        |
| CP-004  | Añadir producto al carrito                    | Validar que el usuario puede agregar productos al carrito solo si tiene su perfil completo.                                        | 11/10/2025  | Backend – Carrito              |
| CP-005  | Crear pedido y finalizar compra               | Verificar que el usuario puede crear un pedido desde el carrito y finalizar compra.                                                | 11/10/2025  | Backend – Pedidos              |
| CP-007  | Validar campo obligatorio en registro (unitaria) | Verificar que la función retorna error si falta el campo correo.                                                                   | 11/10/2025  | Backend - Autenticación        |
| CP-008  | Suma de productos en el carrito (unitaria)    | Comprobar que el subtotal se calcula al agregar dos productos distintos.                                                           | 11/10/2025  | Backend – Carrito              |
| CP-009  | Proceso completo de compra (integración)      | Registrar usuario, iniciar sesión, agregar producto, comprar.                                                                      | 11/10/2025  | Backend – Flujo principal      |
| CP-011  | Validación de email en registro               | Probar que la función de validación detecta emails con formato inválido.                                                           | 11/10/2025  | Backend - Autenticación        |
| CP-012  | Validación de contraseña mínima               | Verificar que la función de registro rechaza contraseñas menores a 8 caracteres.                                                   | 11/10/2025  | Backend - Autenticación        |
| CP-013  | Cálculo de total del pedido                   | Verificar que la función suma subtotales de cada ítem del pedido para obtener el total correcto.                                   | 11/10/2025  | Backend - Pedidos              |
| CP-014  | Eliminación lógica de productos               | Asegurar que la función “eliminar producto” solo marca el estado como “inactivo”, sin borrar el registro.                         | 11/10/2025  | Backend - Productos            |
| CP-015  | Suma de stock al agregar producto             | Probar que la función de inventario suma correctamente el stock al agregar nuevo producto idéntico.                                | 11/10/2025  | Backend - Inventario           |
| CP-016  | Agregar producto repetido al carrito          | Verificar que al agregar el mismo producto dos veces, el sistema incrementa la cantidad en lugar de crear dos líneas distintas.    | 11/10/2025  | Backend – Carrito              |
| CP-017  | Eliminar producto del carrito                 | Comprobar que la función elimina correctamente la línea seleccionada del carrito.                                                  | 11/10/2025  | Backend – Carrito              |
| CP-019  | Generación de email de confirmación de cuenta   | Verificar que la función de envío de correo construye correctamente el asunto, destinatario y cuerpo del mensaje al registrar un usuario. | 11/10/2025  | Backend – Notificaciones / Email |
| CP-020  | Búsqueda por texto parcial                    | Validar que la función de búsqueda retorna productos cuyo nombre contiene el texto ingresado, sin distinguir mayúsculas/minúsculas. | 11/11/2025  | Backend – Búsqueda             |
| CP-021  | Búsqueda sin coincidencias                    | Comprobar que la función retorna lista vacía cuando no hay productos que coincidan con el criterio.                                | 11/11/2025  | Backend – Búsqueda             |

## Casos de Prueba Frontend (a ignorar)

| Id      | Caso de Prueba                      | Descripción                                                                              | Fecha       | Área Funcional / Sub proceso |
|---------|-------------------------------------|------------------------------------------------------------------------------------------|-------------|------------------------------|
| CP-F003 | Filtro de productos por categoría   | Validar que el usuario puede filtrar productos por “tradicional” y “saludable”.          | 11/10/2025  | Frontend- Catálogo           |
| CP-F006 | Editar información de perfil        | Validar que el usuario puede editar su nombre, apellido, teléfono y dirección.           | 11/10/2025  | Frontend - Perfil            |

## Pruebas Pendientes por Implementar

Tras el análisis de la cobertura actual, estas son las pruebas que necesitan ser creadas o completadas.

### Pruebas Faltantes

- **CP-013: Cálculo de total del pedido**
  - **Tarea:** Crear una prueba que verifique que el total final de un pedido se calcula correctamente sumando los subtotales de varios productos diferentes.
- **CP-015: Suma de stock al agregar producto al inventario**
  - **Tarea:** Crear una prueba que asegure que al agregar un producto ya existente al inventario, su `cantidad` (stock) se incrementa correctamente.
- **CP-016: Agregar producto repetido al carrito**
  - **Tarea:** Crear una prueba que verifique que al agregar un producto que ya está en el carrito, el sistema incrementa la cantidad en lugar de añadir una nueva línea.
- **CP-019: Generación de email de confirmación de cuenta**
  - **Tarea:** Crear pruebas que verifiquen que la función de envío de correos se ejecuta y construye el email de confirmación correctamente durante el registro de un usuario.

### Pruebas Incompletas

- **CP-004: Añadir producto al carrito (con perfil completo)**
  - **Tarea:** Modificar la prueba existente para que valide la pre-condición de que el perfil del usuario (nombre, dirección, etc.) debe estar completo para poder añadir productos al carrito.

## Siguientes Pasos

Ahora que tenemos el contexto claro, podemos proceder a:
1.  **Analizar las pruebas existentes** en `tests/` para ver cuáles de estos casos ya están cubiertos.
2.  **Modificar o eliminar** las pruebas que no se alineen con los casos de backend.
3.  **Crear las pruebas faltantes**.

¿Quieres que comience analizando el directorio `tests/` para hacer un mapeo de la cobertura actual?

