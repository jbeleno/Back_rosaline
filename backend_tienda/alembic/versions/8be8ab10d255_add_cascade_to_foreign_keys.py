"""add_cascade_to_foreign_keys

Revision ID: 8be8ab10d255
Revises: b27588c0553a
Create Date: 2025-01-20 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8be8ab10d255'
down_revision: Union[str, None] = 'b27588c0553a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Actualizar foreign key de clientes -> usuarios con CASCADE
    op.drop_constraint('clientes_id_usuario_fkey', 'clientes', type_='foreignkey')
    op.create_foreign_key(
        'clientes_id_usuario_fkey',
        'clientes', 'usuarios',
        ['id_usuario'], ['id_usuario'],
        ondelete='CASCADE'
    )
    
    # Actualizar foreign key de pedidos -> clientes con CASCADE
    op.drop_constraint('pedidos_id_cliente_fkey', 'pedidos', type_='foreignkey')
    op.create_foreign_key(
        'pedidos_id_cliente_fkey',
        'pedidos', 'clientes',
        ['id_cliente'], ['id_cliente'],
        ondelete='CASCADE'
    )
    
    # Actualizar foreign key de detalle_pedidos -> pedidos con CASCADE
    op.drop_constraint('detalle_pedidos_id_pedido_fkey', 'detalle_pedidos', type_='foreignkey')
    op.create_foreign_key(
        'detalle_pedidos_id_pedido_fkey',
        'detalle_pedidos', 'pedidos',
        ['id_pedido'], ['id_pedido'],
        ondelete='CASCADE'
    )
    
    # Actualizar foreign key de carrito -> clientes con CASCADE
    op.drop_constraint('carrito_id_cliente_fkey', 'carrito', type_='foreignkey')
    op.create_foreign_key(
        'carrito_id_cliente_fkey',
        'carrito', 'clientes',
        ['id_cliente'], ['id_cliente'],
        ondelete='CASCADE'
    )
    
    # Actualizar foreign key de detalle_carrito -> carrito con CASCADE
    op.drop_constraint('detalle_carrito_id_carrito_fkey', 'detalle_carrito', type_='foreignkey')
    op.create_foreign_key(
        'detalle_carrito_id_carrito_fkey',
        'detalle_carrito', 'carrito',
        ['id_carrito'], ['id_carrito'],
        ondelete='CASCADE'
    )
    
    # Actualizar foreign key de audit_log -> usuarios con SET NULL (para mantener historial)
    op.drop_constraint('audit_log_usuario_id_fkey', 'audit_log', type_='foreignkey')
    op.create_foreign_key(
        'audit_log_usuario_id_fkey',
        'audit_log', 'usuarios',
        ['usuario_id'], ['id_usuario'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Revertir foreign key de audit_log -> usuarios
    op.drop_constraint('audit_log_usuario_id_fkey', 'audit_log', type_='foreignkey')
    op.create_foreign_key(
        'audit_log_usuario_id_fkey',
        'audit_log', 'usuarios',
        ['usuario_id'], ['id_usuario']
    )
    
    # Revertir foreign key de detalle_carrito -> carrito
    op.drop_constraint('detalle_carrito_id_carrito_fkey', 'detalle_carrito', type_='foreignkey')
    op.create_foreign_key(
        'detalle_carrito_id_carrito_fkey',
        'detalle_carrito', 'carrito',
        ['id_carrito'], ['id_carrito']
    )
    
    # Revertir foreign key de carrito -> clientes
    op.drop_constraint('carrito_id_cliente_fkey', 'carrito', type_='foreignkey')
    op.create_foreign_key(
        'carrito_id_cliente_fkey',
        'carrito', 'clientes',
        ['id_cliente'], ['id_cliente']
    )
    
    # Revertir foreign key de detalle_pedidos -> pedidos
    op.drop_constraint('detalle_pedidos_id_pedido_fkey', 'detalle_pedidos', type_='foreignkey')
    op.create_foreign_key(
        'detalle_pedidos_id_pedido_fkey',
        'detalle_pedidos', 'pedidos',
        ['id_pedido'], ['id_pedido']
    )
    
    # Revertir foreign key de pedidos -> clientes
    op.drop_constraint('pedidos_id_cliente_fkey', 'pedidos', type_='foreignkey')
    op.create_foreign_key(
        'pedidos_id_cliente_fkey',
        'pedidos', 'clientes',
        ['id_cliente'], ['id_cliente']
    )
    
    # Revertir foreign key de clientes -> usuarios
    op.drop_constraint('clientes_id_usuario_fkey', 'clientes', type_='foreignkey')
    op.create_foreign_key(
        'clientes_id_usuario_fkey',
        'clientes', 'usuarios',
        ['id_usuario'], ['id_usuario']
    )

