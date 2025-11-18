"""
Database configuration for the application.

- Configures the SQLAlchemy engine, session, and base for ORM models.
- Optimized for Amazon Aurora PostgreSQL with connection pooling.
- Main dependency: SQLAlchemy
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno desde .env
load_dotenv()

# Lee la URL de la base de datos desde la variable de entorno DATABASE_URL
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError(
        "DATABASE_URL no está configurada. "
        "Por favor, configura la variable de entorno DATABASE_URL."
    )

# Configuración del pool de conexiones para Aurora PostgreSQL
# Optimizado para manejar múltiples workers de Gunicorn
pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "5"))
pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # Reciclar conexiones cada hora

# Crear engine con configuración de pool optimizada para Aurora
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_timeout=pool_timeout,
    pool_recycle=pool_recycle,
    pool_pre_ping=True,  # Verificar conexiones antes de usarlas (importante para Aurora)
    echo=False  # Cambiar a True para debug de queries SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
