import sqlite3
import os

# Ruta a tu base de datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "jesusito_asistencia.db")

def ejecutar_migracion():
    if not os.path.exists(DB_PATH):
        print("No se encontró la base de datos. Ejecuta main.py primero.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Iniciando migración a V1.1...")

    try:
        # 1. Agregar columna 'jornada_base' a empleados si no existe
        try:
            cursor.execute("ALTER TABLE empleados ADD COLUMN jornada_base INTEGER DEFAULT 8")
            print("- Columna 'jornada_base' añadida a empleados.")
        except sqlite3.OperationalError:
            print("- La columna 'jornada_base' ya existía.")

        # 2. Agregar columna 'sucursal' a asistencia si no existe
        try:
            cursor.execute("ALTER TABLE asistencia ADD COLUMN sucursal TEXT DEFAULT 'Matriz'")
            print("- Columna 'sucursal' añadida a asistencia.")
        except sqlite3.OperationalError:
            print("- La columna 'sucursal' ya existía.")

        # 3. Crear la tabla de ajustes si no existe
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
        print("- Tabla 'ajustes' verificada/creada.")

        conn.commit()
        print("\n[ÉXITO] Migración completada. Ahora reinicia main.py.")

    except Exception as e:
        print(f"[ERROR] Durante la migración: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    ejecutar_migracion()