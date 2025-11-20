"""change_token_confirmacion_to_pin

Revision ID: 9263c2bef436
Revises: 8be8ab10d255
Create Date: 2025-01-20 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9263c2bef436'
down_revision: Union[str, None] = '8be8ab10d255'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Cambiar el tipo de columna token_confirmacion de VARCHAR(255) a VARCHAR(6)
    # Primero, limpiar cualquier token existente que no sea de 6 dígitos (por si acaso)
    # Luego cambiar el tipo de columna
    op.execute("""
        UPDATE usuarios 
        SET token_confirmacion = NULL 
        WHERE token_confirmacion IS NOT NULL 
        AND LENGTH(token_confirmacion) != 6
    """)
    
    # Cambiar el tipo de columna
    op.alter_column('usuarios', 'token_confirmacion',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=6),
                    existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Revertir el tipo de columna a VARCHAR(255)
    op.alter_column('usuarios', 'token_confirmacion',
                    existing_type=sa.String(length=6),
                    type_=sa.String(length=255),
                    existing_nullable=True)

