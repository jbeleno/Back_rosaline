# Name: Database Configuration
# Nombre: Configuración de la Base de Datos
# Description: Sets up the SQLAlchemy engine, session, and base for database models.
# Descripción: Configura el motor de SQLAlchemy, la sesión y la base para los modelos de la base de datos.
from sqlalchemy import create_engine
# Name: sqlalchemy (create_engine)
# Nombre: sqlalchemy (create_engine)
# Description: Creates a new SQLAlchemy engine instance for database connection.
# Descripción: Crea una nueva instancia de motor SQLAlchemy para la conexión a la base de datos.
from sqlalchemy.ext.declarative import declarative_base
# Name: sqlalchemy.ext.declarative (declarative_base)
# Nombre: sqlalchemy.ext.declarative (declarative_base)
# Description: Provides a base class for declarative class definitions in SQLAlchemy ORM.
# Descripción: Proporciona una clase base para definiciones declarativas en SQLAlchemy ORM.
from sqlalchemy.orm import sessionmaker
# Name: sqlalchemy.orm (sessionmaker)
# Nombre: sqlalchemy.orm (sessionmaker)
# Description: Factory for creating new SQLAlchemy ORM session objects.
# Descripción: Fábrica para crear nuevos objetos de sesión ORM de SQLAlchemy.

SQLALCHEMY_DATABASE_URL = "postgresql://postgres.ozyjkmvsaogxrmewaafj:RXBq15auhTenFmx4@aws-0-us-east-2.pooler.supabase.com:5432/postgres"


engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
