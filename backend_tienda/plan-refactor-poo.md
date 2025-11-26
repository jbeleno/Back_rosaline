# Plan de Migración a Arquitectura Orientada a Objetos

Este documento detalla los pasos para refactorizar el backend hacia una arquitectura basada en clases sin modificar las rutas, los métodos HTTP ni los contratos de entrada/salida existentes.

## Objetivos

1. Mantener la API pública intacta (endpoints, parámetros, payloads y respuestas).
2. Separar responsabilidades en capas (routers, servicios, repositorios, dominio/core).
3. Mejorar testabilidad y mantenibilidad mediante clases y dependencias explícitas.
4. Alinear el proyecto con prácticas de POO sin interrumpir operaciones actuales.

## Fase 0. Preparación

1. Crear una rama de trabajo: `git checkout -b refactor/oop-architecture`.
2. Ejecutar la suite actual de pruebas para tener una línea base (`pytest`).
3. Revisar `app/main.py` y `app/crud.py` para identificar dependencias y comportamientos críticos.

## Fase 1. Reestructuración de Capas Comunes

1. Mover la inicialización de la app a un nuevo módulo `app/core/app.py` con una función `create_app()` que configure FastAPI, CORS, middlewares y registro de routers.
2. Crear `app/core/config.py` para centralizar variables de entorno y settings.
3. Crear `app/core/dependencies.py` para exponer funciones reutilizables (`get_db`, `get_auth_service`, etc.).

## Fase 2. Routers Modulares

1. Dividir `app/main.py` en routers por dominio dentro de `app/routers/` (usuarios, autenticación, clientes, productos, pedidos, carritos, auditoría).
2. Cada router debe importar los servicios necesarios y exponer exactamente los mismos endpoints actuales.
3. Registrar los routers en `create_app()` y reducir `main.py` a un simple "bootstrap" que llame `create_app()`.

## Fase 3. Repositorios Orientados a Objetos

1. Crear `app/repositories/base.py` con abstracciones comunes (p. ej. clase base con operaciones CRUD genéricas).
2. Implementar repositorios concretos (`UsuarioRepository`, `ProductoRepository`, etc.) que reciban `Session` y encapsulen la interacción con SQLAlchemy.
3. Migrar gradualmente las funciones de `app/crud.py` a estos repositorios, dejando funciones de compatibilidad temporal si es necesario.

## Fase 4. Servicios de Dominio

1. En `app/services/`, definir clases de negocio (`UsuarioService`, `ClienteService`, `PedidoService`, etc.) que usen los repositorios y otras dependencias (por ejemplo, `EmailService`).
2. Trasladar reglas de negocio (validaciones, envío de PIN, auditoría) desde `main.py`/`crud.py` a estos servicios.
3. Añadir proveedores en `core/dependencies.py` para instanciar servicios vía `Depends`.

## Fase 5. Servicios Transversales

1. Refactorizar `app/email_service.py` a una clase `EmailService` configurable e inyectable.
2. Encapsular la lógica de auditoría (`audit.py`) en una clase o manager que controle el contexto y los listeners.
3. Crear `AuthService` para gestionar hashing, creación y verificación de tokens, y dependencias de autorización.

## Fase 6. Limpieza del Código Legacy

1. Una vez que routers, servicios y repositorios estén activos, eliminar `app/crud.py` y referencias obsoletas.
2. Asegurar que `main.py` solo importe y ejecute `create_app()`.
3. Actualizar imports en toda la base de código para usar las nuevas clases.

## Fase 7. Actualización de Documentación

1. Revisar y actualizar `README.md` con el nuevo diagrama de capas y ubicaciones de archivos clave.
2. Documentar el flujo de dependencias y cómo agregar nuevos dominios (`docs/architecture.md` opcional).
3. Confirmar que `.env.example` y otros archivos de configuración reflejan cualquier ajuste realizado.

## Fase 8. Pruebas y Validación Final

1. Actualizar fixtures en `tests/conftest.py` para inyectar servicios/repositorios refactorizados.
2. Añadir pruebas unitarias específicas para servicios y repositorios (mock de servicios transversales cuando aplique).
3. Ejecutar `pytest` y revisar resultados; la suite debe pasar sin cambios en los contratos de la API.
4. Realizar pruebas manuales de los endpoints críticos (usuarios, autenticación, pedidos, carritos).

## Entrega

1. Hacer code review interno y validar que la interfaz pública se mantiene.
2. Preparar resumen de cambios y merge a la rama principal una vez aprobados.
3. Etiquetar el release o versión correspondiente.
