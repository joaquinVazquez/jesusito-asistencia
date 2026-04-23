import sqlite3
from datetime import datetime
from src.models.db_manager import crear_conexion

def registrar_asistencia(empleado_nombre, fecha, hora_ui, tipo_registro):
    """
    Registra la asistencia validando que no existan movimientos duplicados consecutivos.
    Retorna: (bool_exito, str_mensaje)
    """
    hora_segura = datetime.now().strftime("%H:%M:%S")
    
    conn = crear_conexion()
    if conn is None:
        return False, "Error de conexión a la base de datos."
        
    try:
        cursor = conn.cursor()
        
        # 1. Validación Anti-Duplicidad
        cursor.execute("""
            SELECT tipo_registro FROM asistencia 
            WHERE empleado_nombre = ? AND fecha = ? 
            ORDER BY hora DESC LIMIT 1
        """, (empleado_nombre, fecha))
        
        ultimo_registro = cursor.fetchone()
        
        if ultimo_registro:
            ultimo_tipo = ultimo_registro[0]
            if ultimo_tipo == tipo_registro:
                # Personalización del mensaje según el tipo de registro
                if tipo_registro == "Entrada":
                    return False, f"El empleado {empleado_nombre} ya ha sido registrado con Entrada el día de hoy."
                else:
                    return False, f"El empleado {empleado_nombre} ya ha registrado su Salida previamente."
        else:
            # Si no hay registros previos en el día, el primero DEBE ser Entrada
            if tipo_registro == "Salida":
                return False, "Operación denegada. No se puede registrar 'Salida' sin una 'Entrada' previa."

        # 2. Inserción si pasa la validación
        sql_insert = "INSERT INTO asistencia (empleado_nombre, fecha, hora, tipo_registro) VALUES (?, ?, ?, ?)"
        cursor.execute(sql_insert, (empleado_nombre, fecha, hora_segura, tipo_registro))
        conn.commit()
        
        return True, "Registro guardado correctamente."
        
    except sqlite3.Error as e:
        return False, f"Error interno SQL: {e}"
    finally:
        conn.close()

def obtener_ultimo_estado_dia(empleado_nombre, fecha_consulta):
    """Consulta el último movimiento de un empleado en una fecha específica."""
    from src.models.db_manager import crear_conexion
    conn = crear_conexion()
    if not conn: return None
    
    try:
        cursor = conn.cursor()
        # Buscamos el último registro basado en la fecha exacta que se ve en la UI
        cursor.execute("""
            SELECT tipo_registro FROM asistencia 
            WHERE empleado_nombre = ? AND fecha = ? 
            ORDER BY hora DESC LIMIT 1
        """, (empleado_nombre, fecha_consulta))
        
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None
    except:
        return None
    finally:
        conn.close()

def obtener_historial_empleado(empleado_nombre):
    """Recupera todos los registros de un empleado ordenados de forma descendente."""
    conn = crear_conexion()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fecha, hora, tipo_registro 
            FROM asistencia 
            WHERE empleado_nombre = ? 
            ORDER BY fecha DESC, hora DESC
        """, (empleado_nombre,))
        return cursor.fetchall()
    except sqlite3.Error:
        return []
    finally:
        conn.close()

if __name__ == "__main__":
    # Prueba de humo simulando un turno de la pastelería
    print("Iniciando prueba de inserción de datos...")
    registrar_asistencia("Carlos Pastelero", "2026-04-14", "07:55", "Entrada")
    registrar_asistencia("Ana Mostrador", "2026-04-14", "08:02", "Entrada")