# Store Backend (Rosaline Bakery)

Backend de comercio electrónico desarrollado con **FastAPI** para Rosaline Bakery. Tras la refactorización en curso, la aplicación adopta una arquitectura orientada a objetos basada en capas (configuración centralizada, repositorios, servicios y routers) conservando los mismos endpoints y contratos existentes. Permite administrar usuarios, clientes, productos, categorías, pedidos y carritos con autenticación JWT y conexión a PostgreSQL.

## Main Features

- **Users**: Registration, editing, deletion, and authentication.
- **Clients**: Full client management.
- **Products and Categories**: CRUD for products and categories.
- **Orders and Details**: Management of orders and their details.
- **Shopping Cart**: Operations on carts and products in the cart.
- **JWT Authentication**: Secure login.
- **CORS enabled**: Allows requests from any origin (useful for development).

## Project Structure

```
backend_tienda/
│
├── app/
│   ├── core/
│   │   ├── app.py            # FastAPI application factory (create_app)
│   │   ├── config.py         # Centralized settings with Pydantic BaseSettings
│   │   └── dependencies.py   # Dependency providers (DB, repos, services, utilities)
│   ├── repositories/         # Repository layer wrapping persistence logic
│   │   ├── base.py
│   │   ├── usuario_repository.py
│   │   ├── cliente_repository.py
│   │   ├── categoria_repository.py
│   │   ├── producto_repository.py
│   │   ├── pedido_repository.py
│   │   ├── detalle_pedido_repository.py
│   │   └── carrito_repository.py
│   ├── services/             # (En progreso) Servicios de dominio y reglas de negocio
│   ├── main.py               # Punto de entrada legacy con endpoints actuales
│   ├── models.py             # Modelos SQLAlchemy
│   ├── schemas.py            # Esquemas Pydantic
│   ├── crud.py               # Funciones CRUD legacy (en migración a repositorios)
│   ├── database.py           # Configuración de base de datos
│   ├── auth.py               # Autenticación y seguridad (AuthService + helpers)
│   ├── email_service.py      # EmailService (compatibilidad con funciones legacy)
│   ├── audit.py              # Sistema de auditoría con SQLAlchemy events
│   └── __init__.py
├── tests/                    # Suite de pruebas (actualización pendiente)
├── plan-refactor-poo.md      # Plan detallado de migración a arquitectura OOP
├── requirements.txt          # Dependencias del proyecto
├── runtime.txt               # Versión de Python para despliegue
├── pytest.ini                # Configuración de Pytest
└── Procfile                  # Para despliegues en plataformas como Heroku/Render
```

> **Nota:** los endpoints permanecen en `app/main.py` hasta completar la migración a routers modulares. La documentación se irá actualizando conforme avance el plan.

## Installation

1. **Clone the repository:**
   ```bash
   git clone <REPO_URL>
   cd backend_tienda
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The application uses environment variables for configuration. Create a `.env` file in the `backend_tienda` directory:

**Opción 1: Copiar desde el archivo de ejemplo**
```bash
cp .env.example .env
# Luego edita .env con tus valores específicos
```

**Opción 2: Crear manualmente**

```env
# Entorno
APP_ENV=development
PYTHONPATH=./app
DEBUG=True

# Amazon Aurora PostgreSQL
DATABASE_URL=postgresql://postgres:Ecommerce2025!@ecommerce-aurora-db.c5qc4qo884xb.us-east-2.rds.amazonaws.com:5432/postgres

# Seguridad
SECRET_KEY=your-secret-key-here-min-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS
CORS_ORIGINS=*

# Pool de conexiones (opcional)
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=5
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

**Variables requeridas:**
- `DATABASE_URL`: URL de conexión a Amazon Aurora PostgreSQL
  - Formato: `postgresql://usuario:password@host:puerto/base`
  - Ejemplo: `postgresql://postgres:password@ecommerce-aurora-db.c5qc4qo884xb.us-east-2.rds.amazonaws.com:5432/postgres`
- `SECRET_KEY`: Clave secreta para JWT (mínimo 32 caracteres)

**Variables opcionales:**
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Tiempo de expiración del token (default: 60)
- `CORS_ORIGINS`: Orígenes permitidos para CORS (default: "*")
- `DB_POOL_SIZE`: Tamaño del pool de conexiones (default: 10)
- `DB_MAX_OVERFLOW`: Conexiones adicionales permitidas (default: 5)
- `DB_POOL_TIMEOUT`: Timeout del pool en segundos (default: 30)
- `DB_POOL_RECYCLE`: Tiempo de reciclaje de conexiones en segundos (default: 3600)

## Running

To start the development server:

Opción recomendada (usando la factoría `create_app`):

```bash
cd backend_tienda
uvicorn app.core.app:create_app --factory --reload
```

También puedes seguir utilizando el punto de entrada legacy mientras se completa la modularización:

```bash
cd backend_tienda
uvicorn app.main:app --reload
```

La API estará disponible en [http://localhost:8000](http://localhost:8000).

## Conexión a Amazon Aurora PostgreSQL

El proyecto está configurado para conectarse a Amazon Aurora PostgreSQL. Asegúrate de:

1. **Verificar conectividad desde tu máquina/servidor:**
   ```bash
   # Probar conexión con psql (si está instalado)
   psql -h ecommerce-aurora-db.c5qc4qo884xb.us-east-2.rds.amazonaws.com -U postgres -d postgres -p 5432
   ```

2. **Configurar Security Groups en AWS:**
   - Asegúrate de que el Security Group de Aurora permita conexiones desde tu IP o instancia EC2
   - Puerto: 5432
   - Protocolo: TCP

3. **Verificar que las tablas existan:**
   - El proyecto creará automáticamente las tablas si no existen (solo en desarrollo)
   - En producción, usa migraciones con Alembic o crea las tablas manualmente

4. **Comandos útiles para conectarse a Aurora:**
   ```bash
   # Usando psql
   psql "postgresql://postgres:Ecommerce2025!@ecommerce-aurora-db.c5qc4qo884xb.us-east-2.rds.amazonaws.com:5432/postgres"
   
   # Verificar conexión desde Python
   python -c "from app.database import engine; engine.connect(); print('Conexión exitosa')"
   ```

## Main Endpoints

Some available endpoints:

- `POST /usuarios/` - Create user
- `POST /login` - Login
- `GET /clientes/` - List clients
- `POST /productos/` - Create product
- `GET /productos/` - List products
- `POST /pedidos/` - Create order
- `GET /pedidos/` - List orders
- ...and many more for CRUD of each entity

The interactive API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs) thanks to Swagger.

## Deployment

### Render.com

El proyecto está configurado para desplegarse en Render. Sigue estos pasos:

1. **Conecta tu repositorio GitHub a Render:**
   - Inicia sesión en [Render](https://render.com)
   - Ve a "New" → "Web Service"
   - Conecta tu repositorio de GitHub

2. **Configura el servicio:**
   - **Build Command:** `pip install -r backend_tienda/requirements.txt`
   - **Start Command:** `cd backend_tienda && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3

3. **Configura las variables de entorno en Render:**
   - `DATABASE_URL`: Tu URL de Amazon Aurora PostgreSQL
   - `SECRET_KEY`: Clave secreta para JWT (genera una segura)
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: 60 (opcional)
   - `CORS_ORIGINS`: "*" o URLs específicas de tu frontend (opcional)

4. **Despliegue:**
   - Render detectará automáticamente el `render.yaml` en la raíz del proyecto
   - O puedes configurar manualmente usando las instrucciones anteriores

### Otras plataformas

Incluye un `Procfile` compatible con Heroku y otras plataformas similares.

## License

This project is under the MIT license.

## Used Libraries

- **FastAPI**: Web framework for building APIs.
- **SQLAlchemy**: ORM for database management.
- **Pydantic**: Data validation and serialization.
- **Uvicorn**: ASGI server for running FastAPI.
- **python-jose**: JWT token encoding and decoding.
- **passlib**: Password hashing utilities.
- **psycopg2**: PostgreSQL database adapter.
- **python-dotenv**: Environment variable management (if used).
- **CORS Middleware**: For handling cross-origin requests.
