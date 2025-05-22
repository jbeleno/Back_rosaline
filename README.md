# Backend Tienda

Este es un backend desarrollado con **FastAPI** para la gestión de una tienda en línea. Permite la administración de usuarios, clientes, productos, categorías, pedidos y carritos de compra, integrando autenticación y conexión a base de datos PostgreSQL.

## Características principales

- **Usuarios**: Registro, edición, eliminación y autenticación.
- **Clientes**: Gestión completa de clientes.
- **Productos y Categorías**: CRUD de productos y categorías.
- **Pedidos y Detalles**: Gestión de pedidos y sus detalles.
- **Carrito de compras**: Operaciones sobre carritos y productos en el carrito.
- **Autenticación JWT**: Inicio de sesión seguro.
- **CORS habilitado**: Permite peticiones desde cualquier origen (útil para desarrollo).

## Estructura del proyecto

```
backend_tienda/
│
├── app/
│   ├── main.py           # Puntos de entrada y rutas de la API
│   ├── models.py         # Modelos de SQLAlchemy
│   ├── schemas.py        # Esquemas de Pydantic
│   ├── crud.py           # Operaciones CRUD
│   ├── database.py       # Configuración de la base de datos
│   ├── auth.py           # Autenticación y seguridad
│   └── __init__.py
├── requirements.txt      # Dependencias del proyecto
└── Procfile              # Para despliegue en plataformas como Heroku
```

## Instalación

1. **Clona el repositorio:**
   ```bash
   git clone <URL_DEL_REPO>
   cd backend_tienda
   ```

2. **Crea un entorno virtual (opcional pero recomendado):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuración

La conexión a la base de datos está definida en `app/database.py`. Por defecto, utiliza PostgreSQL en Supabase:

```python
SQLALCHEMY_DATABASE_URL = "postgresql://<usuario>:<contraseña>@<host>:<puerto>/<db>"
```

Modifica esta URL si necesitas conectar a otra base de datos.

## Ejecución

Para iniciar el servidor de desarrollo:

```bash
uvicorn app.main:app --reload
```

La API estará disponible en: [http://localhost:8000](http://localhost:8000)

## Endpoints principales

Algunos endpoints disponibles:

- `POST /usuarios/` - Crear usuario
- `POST /login` - Iniciar sesión
- `GET /clientes/` - Listar clientes
- `POST /productos/` - Crear producto
- `GET /productos/` - Listar productos
- `POST /pedidos/` - Crear pedido
- `GET /pedidos/` - Listar pedidos
- ...y muchos más para CRUD de cada entidad

La documentación interactiva de la API está disponible en [http://localhost:8000/docs](http://localhost:8000/docs) gracias a Swagger.

## Despliegue

Incluye un `Procfile` para despliegue en plataformas como Heroku.

## Licencia

Este proyecto está bajo la licencia MIT.
