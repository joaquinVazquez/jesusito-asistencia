import psycopg2
import os
from dotenv import load_dotenv

# Carga las variables de tu archivo .env
load_dotenv()

def probar_conexion():
    print("Iniciando conexión a Supabase vía Pooler (IPv4)...")
    
    uri = os.getenv("DATABASE_URL")
    
    if not uri:
        print("[ERROR] No se encontró la variable DATABASE_URL en el archivo .env")
        return

    try:
        # Forzamos sslmode='require', vital para Supabase
        conn = psycopg2.connect(uri, sslmode='require')
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version_db = cursor.fetchone()
        
        print("\n[ÉXITO] Túnel de infraestructura establecido.")
        print(f"Versión del motor: {version_db[0]}")
        
        cursor.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"\n[Fallo Operacional] PostgreSQL rechazó la conexión:\n{e}")
        print("-> Verifica que la URI en el .env tenga el puerto 6543.")
    except Exception as e:
        print(f"\n[Error Crítico] {e}")

if __name__ == "__main__":
    probar_conexion()