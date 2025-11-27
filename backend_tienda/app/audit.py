"""
Sistema de auditoría usando SQLAlchemy event listeners.
Captura información del contexto (usuario, IP, endpoint) y actualiza los registros creados por triggers.
"""

from datetime import datetime, timedelta
from sqlalchemy import event, text
from . import models

# Contexto global para almacenar información de la request actual
class AuditContext:
    def __init__(self):
        self.user_id = None
        self.user_email = None
        self.ip_address = None
        self.endpoint = None
        self.reset()
    
    def reset(self):
        self.user_id = None
        self.user_email = None
        self.ip_address = None
        self.endpoint = None

# Contexto global (thread-local)
audit_context = AuditContext()

def set_audit_context(user_id=None, user_email=None, ip_address=None, endpoint=None):
    """Establece el contexto de auditoría para la request actual."""
    audit_context.user_id = user_id
    audit_context.user_email = user_email
    audit_context.ip_address = ip_address
    audit_context.endpoint = endpoint

def clear_audit_context():
    """Limpia el contexto de auditoría."""
    audit_context.reset()

def get_record_id(instance):
    """Obtiene el ID del registro según el tipo de modelo."""
    if hasattr(instance, 'id_usuario'):
        return instance.id_usuario
    elif hasattr(instance, 'id_cliente'):
        return instance.id_cliente
    elif hasattr(instance, 'id_categoria'):
        return instance.id_categoria
    elif hasattr(instance, 'id_producto'):
        return instance.id_producto
    elif hasattr(instance, 'id_pedido'):
        return instance.id_pedido
    elif hasattr(instance, 'id_detalle'):
        return instance.id_detalle
    elif hasattr(instance, 'id_carrito'):
        return instance.id_carrito
    elif hasattr(instance, 'id_detalle_carrito'):
        return instance.id_detalle_carrito
    return None

def get_table_name(instance):
    """Obtiene el nombre de la tabla del modelo."""
    if hasattr(instance, '__tablename__'):
        return instance.__tablename__
    return None

def update_audit_log(connection, instance, operation: str):
    """Actualiza el registro de auditoría creado por el trigger con información del contexto."""
    try:
        # Obtener información del contexto
        user_id = audit_context.user_id
        user_email = audit_context.user_email
        ip_address = audit_context.ip_address
        endpoint = audit_context.endpoint
        
        if not user_id and not user_email and not ip_address and not endpoint:
            return  # No hay contexto que actualizar
        
        # Obtener ID del registro y nombre de tabla
        registro_id = get_record_id(instance)
        tabla_nombre = get_table_name(instance)
        
        if registro_id is None or tabla_nombre is None:
            return  # No se puede actualizar sin esta información
        
        # Actualizar registro existente en audit_log con información del contexto
        # Esto actualiza el registro creado por el trigger con información adicional
        # Buscamos el registro más reciente (últimos 2 segundos) para ese registro y operación
        # Usamos una subconsulta para obtener el ID del registro más reciente
        connection.execute(
            text("""
                UPDATE audit_log 
                SET usuario_id = :user_id,
                    usuario_email = :user_email,
                    ip_address = :ip_address,
                    endpoint = :endpoint
                WHERE id_audit = (
                    SELECT id_audit
                    FROM audit_log
                    WHERE tabla_nombre = :tabla_nombre
                        AND registro_id = :registro_id
                        AND accion = :accion
                        AND fecha_accion > :threshold
                    ORDER BY fecha_accion DESC
                    LIMIT 1
                )
            """),
            {
                'user_id': user_id,
                'user_email': user_email,
                'ip_address': ip_address,
                'endpoint': endpoint,
                'tabla_nombre': tabla_nombre,
                'registro_id': registro_id,
                'accion': operation,
                'threshold': (datetime.utcnow() - timedelta(seconds=2)).strftime('%Y-%m-%d %H:%M:%S')
            }
        )
        # NO hacer commit aquí - dejar que la transacción principal lo maneje
    except Exception as e:
        # No fallar la operación principal si hay error en auditoría
        # NO hacer rollback aquí - dejar que la transacción principal lo maneje
        print(f"Error en auditoría: {e}")

# Registrar listeners para cada modelo usando funciones con closure
def make_listener(op_type):
    """Crea un listener para un tipo de operación específico."""
    def listener(mapper, connection, target):
        try:
            update_audit_log(connection, target, op_type)
        except Exception as e:
            # No fallar la operación principal si hay error en auditoría
            print(f"Error en listener de auditoría ({op_type}): {e}")
    return listener

# Registrar listeners para cada modelo
tables_to_audit = [
    models.Usuario,
    models.Cliente,
    models.Categoria,
    models.Producto,
    models.Pedido,
    models.DetallePedido,
    models.Carrito,
    models.DetalleCarrito
]

for model in tables_to_audit:
    event.listens_for(model, 'after_insert', propagate=True)(make_listener('INSERT'))
    event.listens_for(model, 'after_update', propagate=True)(make_listener('UPDATE'))
    event.listens_for(model, 'after_delete', propagate=True)(make_listener('DELETE'))
