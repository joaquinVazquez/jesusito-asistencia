import sqlite3
import os

# Localizamos la base de datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "jesusito_asistencia.db")

def reiniciar_operaciones():
    if not os.path.exists(DB_PATH):
        print("[!] No se encontró la base de datos.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Borramos solo el historial de entradas y salidas
        cursor.execute("DELETE FROM asistencia")
        
        # 2. Opcional: Si quieres borrar empleados pero NO el PIN, descomenta la siguiente línea:
        # cursor.execute("DELETE FROM empleados")
        
        conn.commit()
        print("[ÉXITO] Historial de asistencia eliminado. El sistema está en CERO.")
    except Exception as e:
        print(f"[ERROR] No se pudo limpiar la base de datos: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    confirmacion = input("¿Estás seguro de borrar TODO el historial de asistencia? (s/n): ")
    if confirmacion.lower() == 's':
        reiniciar_operaciones()