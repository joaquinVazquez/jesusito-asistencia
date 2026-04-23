import sqlite3
import os

# Localizamos la base de datos actual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "jesusito_asistencia.db")

def inicializar_seguridad():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Creamos una tabla genérica para configuraciones del sistema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            parametro TEXT PRIMARY KEY,
            valor TEXT
        )
    """)
    
    # Insertamos el PIN inicial (puedes cambiar '1234' por el que desees ahora)
    cursor.execute("INSERT OR IGNORE INTO config (parametro, valor) VALUES ('pin_admin', '1234')")
    
    conn.commit()
    conn.close()
    print("[LOG] Tabla de configuración lista y PIN inicial establecido.")

if __name__ == "__main__":
    inicializar_seguridad()