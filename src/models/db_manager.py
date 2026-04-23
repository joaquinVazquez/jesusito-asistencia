import sqlite3
import os
import sys

def obtener_ruta_db():
    if getattr(sys, 'frozen', False):
        # Si es .exe, la carpeta data estará junto al .exe
        base_path = os.path.dirname(sys.executable)
    else:
        # En desarrollo
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    ruta_data = os.path.join(base_path, "data")
    if not os.path.exists(ruta_data):
        try:
            os.makedirs(ruta_data)
        except:
            # Si falla (por permisos en C:), lo crea en el Escritorio del usuario como fallback
            ruta_data = os.path.join(os.path.expanduser("~"), "Desktop", "Jesusito_Data")
            if not os.path.exists(ruta_data): os.makedirs(ruta_data)

    return os.path.join(ruta_data, "jesusito_asistencia.db")

def crear_conexion():
    db_path = obtener_ruta_db()
    conn = sqlite3.connect(db_path)
    return conn

def inicializar_base_de_datos():
    """Crea las tablas desde cero si no existen."""
    conn = crear_conexion()
    cursor = conn.cursor()
    
    # Tabla Empleados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            pago_hora REAL DEFAULT 0.0,
            estatus TEXT DEFAULT 'Activo'
        )
    """)
    
    # Tabla Asistencia
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asistencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_nombre TEXT,
            fecha TEXT,
            hora TEXT,
            tipo_registro TEXT,
            FOREIGN KEY(empleado_nombre) REFERENCES empleados(nombre)
        )
    """)
    
    # Tabla Configuración (PIN)
    cursor.execute("CREATE TABLE IF NOT EXISTS config (parametro TEXT PRIMARY KEY, valor TEXT)")
    cursor.execute("INSERT OR IGNORE INTO config (parametro, valor) VALUES ('pin_admin', '1234')")
    
    conn.commit()
    conn.close()
    print("[SISTEMA] Base de datos verificada/creada con éxito.")