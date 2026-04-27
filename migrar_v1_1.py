import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "jesusito_asistencia.db")

def actualizar_tabla_empleados_v2():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Añadimos los campos que solicitaste
    nuevas_columnas = {
        "direccion": "TEXT DEFAULT 'Sin registro'",
        "fecha_nacimiento": "TEXT DEFAULT ''",
        "fecha_ingreso": "TEXT DEFAULT ''",
        "expediente": "TEXT DEFAULT ''"
    }
    
    print("Migrando tabla de empleados (Expedientes y Fechas)...")
    for col, tipo in nuevas_columnas.items():
        try:
            cursor.execute(f"ALTER TABLE empleados ADD COLUMN {col} {tipo}")
            print(f"[+] Columna '{col}' añadida correctamente.")
        except sqlite3.OperationalError:
            print(f"[-] Columna '{col}' ya existe, omitiendo.")
            
    conn.commit()
    conn.close()
    print("Migración de expedientes completada con éxito.")

if __name__ == "__main__":
    actualizar_tabla_empleados_v2()