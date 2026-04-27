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
    conn = crear_conexion()
    cursor = conn.cursor()
    
    # 1. Creación base de Empleados (Solo lo esencial)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        )
    """)
    
    # --- MOTOR DE AUTO-MIGRACIÓN PARA EMPLEADOS ---
    columnas_requeridas = {
        "telefono": "TEXT DEFAULT 'Sin registro'",
        "rol": "TEXT DEFAULT 'General'",
        "direccion": "TEXT DEFAULT 'Sin registro'",
        "fecha_nacimiento": "TEXT DEFAULT ''",
        "fecha_ingreso": "TEXT DEFAULT ''",
        "expediente": "TEXT DEFAULT ''",
        "pago_hora": "REAL DEFAULT 0.0",
        "jornada_base": "INTEGER DEFAULT 8",
        "estatus": "TEXT DEFAULT 'Activo'"
    }
    
    # Obtenemos las columnas que realmente existen en el archivo .db
    cursor.execute("PRAGMA table_info(empleados)")
    columnas_actuales = [row[1] for row in cursor.fetchall()]
    
    # Inyectamos automáticamente las que falten
    for col, definicion in columnas_requeridas.items():
        if col not in columnas_actuales:
            try:
                cursor.execute(f"ALTER TABLE empleados ADD COLUMN {col} {definicion}")
                print(f"[SISTEMA] Columna faltante agregada: {col}")
            except Exception as e:
                print(f"[ERROR] No se pudo agregar {col}: {e}")
    # ----------------------------------------------

    # 2. Tabla Asistencia
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asistencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_nombre TEXT,
            fecha TEXT,
            hora TEXT,
            tipo_registro TEXT,
            sucursal TEXT DEFAULT 'Matriz',
            FOREIGN KEY(empleado_nombre) REFERENCES empleados(nombre)
        )
    """)
    
    # 3. Tabla Ajustes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ajustes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_nombre TEXT,
            fecha TEXT,
            monto REAL,
            tipo TEXT,
            motivo TEXT,
            FOREIGN KEY(empleado_nombre) REFERENCES empleados(nombre)
        )
    """)
    
    # 4. Tabla Configuración
    cursor.execute("CREATE TABLE IF NOT EXISTS config (parametro TEXT PRIMARY KEY, valor TEXT)")
    cursor.execute("INSERT OR IGNORE INTO config (parametro, valor) VALUES ('pin_admin', '1234')")
    
    conn.commit()
    conn.close()
    print("[SISTEMA] Base de datos verificada y auto-migrada con éxito.")