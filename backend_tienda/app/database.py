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
from .core.config import get_settings

# Cargar variables de entorno desde .env
load_dotenv()

settings = get_settings()
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

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
    pool_size=10, # You can make these configurable in Settings too if needed
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
