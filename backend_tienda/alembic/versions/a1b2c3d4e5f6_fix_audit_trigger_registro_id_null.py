"""fix_audit_trigger_registro_id_null

Revision ID: a1b2c3d4e5f6
Revises: 9263c2bef436
Create Date: 2025-11-21 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9263c2bef436'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Fix audit trigger to handle registro_id correctly."""
    # Eliminar triggers existentes
    op.execute("""
        DROP TRIGGER IF EXISTS audit_trigger ON carrito;
        DROP TRIGGER IF EXISTS audit_trigger ON detalle_carrito;
        DROP TRIGGER IF EXISTS audit_trigger ON usuarios;
        DROP TRIGGER IF EXISTS audit_trigger ON clientes;
        DROP TRIGGER IF EXISTS audit_trigger ON categorias;
        DROP TRIGGER IF EXISTS audit_trigger ON productos;
        DROP TRIGGER IF EXISTS audit_trigger ON pedidos;
        DROP TRIGGER IF EXISTS audit_trigger ON detalle_pedidos;
    """)
    
    # Eliminar función existente
    op.execute("DROP FUNCTION IF EXISTS audit_trigger_function() CASCADE;")
    
    # Crear nueva función de trigger que maneje correctamente todas las tablas
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_trigger_function()
        RETURNS TRIGGER AS $$
        DECLARE
            registro_id_val INTEGER;
            old_data JSONB;
            new_data JSONB;
            changed_fields JSONB;
        BEGIN
            -- Obtener el ID según la tabla
            IF TG_TABLE_NAME = 'usuarios' THEN
                registro_id_val := NEW.id_usuario;
            ELSIF TG_TABLE_NAME = 'clientes' THEN
                registro_id_val := NEW.id_cliente;
            ELSIF TG_TABLE_NAME = 'categorias' THEN
                registro_id_val := NEW.id_categoria;
            ELSIF TG_TABLE_NAME = 'productos' THEN
                registro_id_val := NEW.id_producto;
            ELSIF TG_TABLE_NAME = 'pedidos' THEN
                registro_id_val := NEW.id_pedido;
            ELSIF TG_TABLE_NAME = 'detalle_pedidos' THEN
                registro_id_val := NEW.id_detalle;
            ELSIF TG_TABLE_NAME = 'carrito' THEN
                registro_id_val := NEW.id_carrito;
            ELSIF TG_TABLE_NAME = 'detalle_carrito' THEN
                registro_id_val := NEW.id_detalle_carrito;
            ELSE
                registro_id_val := NULL;
            END IF;
            
            -- Para DELETE, usar OLD en lugar de NEW
            IF TG_OP = 'DELETE' THEN
                IF TG_TABLE_NAME = 'usuarios' THEN
                    registro_id_val := OLD.id_usuario;
                ELSIF TG_TABLE_NAME = 'clientes' THEN
                    registro_id_val := OLD.id_cliente;
                ELSIF TG_TABLE_NAME = 'categorias' THEN
                    registro_id_val := OLD.id_categoria;
                ELSIF TG_TABLE_NAME = 'productos' THEN
                    registro_id_val := OLD.id_producto;
                ELSIF TG_TABLE_NAME = 'pedidos' THEN
                    registro_id_val := OLD.id_pedido;
                ELSIF TG_TABLE_NAME = 'detalle_pedidos' THEN
                    registro_id_val := OLD.id_detalle;
                ELSIF TG_TABLE_NAME = 'carrito' THEN
                    registro_id_val := OLD.id_carrito;
                ELSIF TG_TABLE_NAME = 'detalle_carrito' THEN
                    registro_id_val := OLD.id_detalle_carrito;
                END IF;
            END IF;
            
            -- Solo insertar si tenemos un registro_id válido
            IF registro_id_val IS NULL THEN
                RETURN COALESCE(NEW, OLD);
            END IF;
            
            -- Preparar datos según la operación
            IF TG_OP = 'INSERT' THEN
                new_data := to_jsonb(NEW);
                old_data := NULL;
                changed_fields := NULL;
            ELSIF TG_OP = 'UPDATE' THEN
                old_data := to_jsonb(OLD);
                new_data := to_jsonb(NEW);
                -- Calcular campos que cambiaron
                changed_fields := (
                    SELECT jsonb_object_agg(key, value)
                    FROM jsonb_each(new_data)
                    WHERE value IS DISTINCT FROM (old_data->key)
                );
            ELSIF TG_OP = 'DELETE' THEN
                old_data := to_jsonb(OLD);
                new_data := NULL;
                changed_fields := NULL;
            END IF;
            
            -- Insertar en audit_log
            INSERT INTO audit_log (
                tabla_nombre,
                registro_id,
                accion,
                datos_anteriores,
                datos_nuevos,
                cambios,
                fecha_accion
            ) VALUES (
                TG_TABLE_NAME,
                registro_id_val,
                TG_OP,
                old_data,
                new_data,
                changed_fields,
                CURRENT_TIMESTAMP
            );
            
            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Recrear triggers en todas las tablas
    op.execute("""
        CREATE TRIGGER audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON carrito
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
        
        CREATE TRIGGER audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON detalle_carrito
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
        
        CREATE TRIGGER audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON usuarios
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
        
        CREATE TRIGGER audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON clientes
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
        
        CREATE TRIGGER audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON categorias
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
        
        CREATE TRIGGER audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON productos
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
        
        CREATE TRIGGER audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON pedidos
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
        
        CREATE TRIGGER audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON detalle_pedidos
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
    """)


def downgrade() -> None:
    """Downgrade schema - Revert audit trigger changes."""
    # Eliminar triggers
    op.execute("""
        DROP TRIGGER IF EXISTS audit_trigger ON carrito;
        DROP TRIGGER IF EXISTS audit_trigger ON detalle_carrito;
        DROP TRIGGER IF EXISTS audit_trigger ON usuarios;
        DROP TRIGGER IF EXISTS audit_trigger ON clientes;
        DROP TRIGGER IF EXISTS audit_trigger ON categorias;
        DROP TRIGGER IF EXISTS audit_trigger ON productos;
        DROP TRIGGER IF EXISTS audit_trigger ON pedidos;
        DROP TRIGGER IF EXISTS audit_trigger ON detalle_pedidos;
    """)
    
    # Eliminar función
    op.execute("DROP FUNCTION IF EXISTS audit_trigger_function() CASCADE;")
    
    # Nota: No podemos recrear la función anterior automáticamente
    # porque no sabemos cómo estaba definida originalmente
    # El usuario deberá restaurarla manualmente si es necesario

