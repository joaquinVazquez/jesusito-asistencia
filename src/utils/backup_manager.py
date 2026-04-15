import shutil
import os
from datetime import datetime

# Rutas del sistema
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "jesusito_asistencia.db")
BACKUP_DIR = os.path.join(BASE_DIR, "backups", "local")

# [!] CONFIGURACIÓN DE NUBE: Asegúrate de que esta carpeta exista
RUTA_NUBE = r"C:\Users\lenovo\Documents\Pasteleria_Backups_Nube" 

def ejecutar_respaldo_total(): # <--- ESTE NOMBRE DEBE SER EXACTO
    """Genera el respaldo local y lo replica en la carpeta de la nube."""
    if not os.path.exists(DB_PATH):
        print("[ERROR] No se encontró la base de datos origen.")
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"backup_asistencia_{timestamp}.db"
    ruta_local = os.path.join(BACKUP_DIR, nombre_archivo)

    try:
        # 1. Respaldo Local
        shutil.copy2(DB_PATH, ruta_local)
        
        # 2. Respaldo Cloud (solo si la ruta existe)
        if os.path.exists(RUTA_NUBE):
            ruta_nube_final = os.path.join(RUTA_NUBE, nombre_archivo)
            shutil.copy2(DB_PATH, ruta_nube_final)
            return True
        else:
            # Si no hay nube, el local fue exitoso, retornamos True para no alarmar al UI
            # pero notificamos en consola.
            print(f"[AVISO] Nube no disponible, local guardado: {nombre_archivo}")
            return True

    except Exception as e:
        print(f"[ERROR CRÍTICO] Fallo en respaldo: {e}")
        return False

if __name__ == "__main__":
    ejecutar_respaldo_total()