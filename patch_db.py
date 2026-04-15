import sqlite3
import os

# Ruta exacta a la base de datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "jesusito_asistencia.db")

def aplicar_parche():
    print("Conectando a la base de datos...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Instrucción para agregar la columna faltante
        cursor.execute("ALTER TABLE empleados ADD COLUMN pago_hora REAL DEFAULT 0.0;")
        conn.commit()
        print("[ÉXITO] Columna 'pago_hora' agregada correctamente a la tabla 'empleados'.")
    except sqlite3.OperationalError as e:
        print(f"[STATUS] No se aplicó el parche. Razón: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    aplicar_parche()