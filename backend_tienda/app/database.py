"""
Database configuration for the application.

- Configures the SQLAlchemy engine, session, and base for ORM models.
- Main dependency: SQLAlchemy
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://postgres.ozyjkmvsaogxrmewaafj:RXBq15auhTenFmx4@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
