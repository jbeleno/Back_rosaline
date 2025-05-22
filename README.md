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
│   └── __init__.py
├── requirements.txt      # Project dependencies
└── Procfile              # For deployment on platforms like Heroku
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

The database connection is defined in `app/database.py`. By default, it uses PostgreSQL on Supabase:

```python
SQLALCHEMY_DATABASE_URL = "postgresql://<user>:<password>@<host>:<port>/<db>"
```

Modify this URL if you need to connect to another database.

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

Includes a `Procfile` for deployment on platforms like Heroku.

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
