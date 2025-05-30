"""
Database configuration for the application.

- Configures the SQLAlchemy engine, session, and base for ORM models.
- Main dependency: SQLAlchemy
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Lee la URL de la base de datos desde la variable de entorno DATABASE_URL
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
