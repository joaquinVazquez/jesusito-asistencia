import sqlite3
from datetime import datetime
from src.models.db_manager import crear_conexion

def registrar_asistencia(empleado_nombre, fecha, hora_ui, tipo_registro):
    """Registra la asistencia forzando la hora del sistema (Candado de Seguridad)."""
    # SOBRESCRIBIMOS la hora de la interfaz con la hora exacta del servidor
    hora_segura = datetime.now().strftime("%H:%M:%S")
    
    conn = crear_conexion()
    if conn is not None:
        try:
            cursor = conn.cursor()
            sql_insert = """INSERT INTO asistencia 
                            (empleado_nombre, fecha, hora, tipo_registro) 
                            VALUES (?, ?, ?, ?)"""
            cursor.execute(sql_insert, (empleado_nombre, fecha, hora_segura, tipo_registro))
            conn.commit()
            print(f"[ÉXITO] Asistencia de {empleado_nombre}: {tipo_registro} a las {hora_segura}")
            return True
        except sqlite3.Error as e:
            print(f"[ERROR SQL] No se pudo guardar la asistencia: {e}")
            return False
        finally:
            conn.close()
    return False

if __name__ == "__main__":
    # Prueba de humo simulando un turno de la pastelería
    print("Iniciando prueba de inserción de datos...")
    registrar_asistencia("Carlos Pastelero", "2026-04-14", "07:55", "Entrada")
    registrar_asistencia("Ana Mostrador", "2026-04-14", "08:02", "Entrada")