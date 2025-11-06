# Store Backend

This is a backend developed with **FastAPI** for managing an online store. It allows the administration of users, clients, products, categories, orders, and shopping carts, integrating authentication and connection to a PostgreSQL database.

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
│   ├── main.py           # API entry point and routes
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   ├── crud.py           # CRUD operations
│   ├── database.py       # Database configuration
│   ├── auth.py           # Authentication and security
│   ├── audit.py          # Auditing system
│   └── __init__.py
├── tests/                # Test suite
├── requirements.txt      # Project dependencies
├── runtime.txt          # Python version for deployment
├── pytest.ini          # Pytest configuration
└── Procfile             # For deployment on platforms like Heroku/Render
```

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

```env
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-secret-key-here-min-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=*
```

**Variables requeridas:**
- `DATABASE_URL`: URL de conexión a PostgreSQL (Supabase)
- `SECRET_KEY`: Clave secreta para JWT (mínimo 32 caracteres)

**Variables opcionales:**
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Tiempo de expiración del token (default: 60)
- `CORS_ORIGINS`: Orígenes permitidos para CORS (default: "*")

## Running

To start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at: [http://localhost:8000](http://localhost:8000)

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
   - `DATABASE_URL`: Tu URL de Supabase PostgreSQL
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
