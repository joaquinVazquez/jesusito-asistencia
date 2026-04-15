import sqlite3
import os

# 1. Calculamos la ruta absoluta hacia la carpeta 'data'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "jesusito_asistencia.db")

def crear_conexion():
    """Genera y retorna la conexión a la base de datos SQLite."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except sqlite3.Error as e:
        print(f"[ERROR CRÍTICO] Fallo de conexión a la BD: {e}")
    return conn

def inicializar_base_datos():
    """Crea las tablas del sistema si no existen."""
    
    # Tabla 1: Catálogo de Empleados
    sql_crear_empleados = """
    CREATE TABLE IF NOT EXISTS empleados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        estatus TEXT DEFAULT 'Activo'
    );
    """
    
    # Tabla 2: Registro de Asistencias
    sql_crear_asistencia = """
    CREATE TABLE IF NOT EXISTS asistencia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empleado_nombre TEXT NOT NULL,
        fecha TEXT NOT NULL,
        hora TEXT NOT NULL,
        tipo_registro TEXT NOT NULL
    );
    """
    
    conn = crear_conexion()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Ejecutamos la creación de ambas tablas
            cursor.execute(sql_crear_empleados)
            cursor.execute(sql_crear_asistencia)
            conn.commit()
            print(f"[SISTEMA] Motor de base de datos actualizado en: {DB_PATH}")
        except sqlite3.Error as e:
            print(f"[ERROR SQL] Fallo al estructurar tablas: {e}")
        finally:
            conn.close()
    else:
        print("[SISTEMA] Abortando inicialización por falta de conexión.")

if __name__ == "__main__":
    # Esto solo se ejecuta si corremos este archivo directamente para probar
    inicializar_base_datos()