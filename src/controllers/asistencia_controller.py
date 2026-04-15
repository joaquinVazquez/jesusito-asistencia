import sqlite3
# Importamos la conexión desde nuestro modelo
from src.models.db_manager import crear_conexion

def registrar_asistencia(nombre, fecha, hora, tipo_registro):
    """Inserta de forma segura un nuevo registro en la base de datos."""
    conn = crear_conexion()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Uso de '?' para sanitizar los inputs y prevenir inyección SQL
            sql_insert = """
            INSERT INTO asistencia (empleado_nombre, fecha, hora, tipo_registro)
            VALUES (?, ?, ?, ?)
            """
            valores = (nombre, fecha, hora, tipo_registro)
            cursor.execute(sql_insert, valores)
            conn.commit()
            print(f"[ÉXITO] Registro guardado: {nombre} | {tipo_registro} | {hora}")
            return True
        except sqlite3.Error as e:
            print(f"[ERROR SQL] Fallo al insertar el registro: {e}")
            return False
        finally:
            conn.close()
    return False

if __name__ == "__main__":
    # Prueba de humo simulando un turno de la pastelería
    print("Iniciando prueba de inserción de datos...")
    registrar_asistencia("Carlos Pastelero", "2026-04-14", "07:55", "Entrada")
    registrar_asistencia("Ana Mostrador", "2026-04-14", "08:02", "Entrada")