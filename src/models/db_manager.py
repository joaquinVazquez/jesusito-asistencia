import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def obtener_conexion_pg():
    """Establece conexión con Supabase usando la URI completa."""
    uri = os.getenv("DATABASE_URL")
    if not uri:
        print("[ERROR] No se encontró DATABASE_URL en el archivo .env")
        return None
        
    try:
        # sslmode='require' es obligatorio para el pooler de Supabase
        conn = psycopg2.connect(uri, sslmode='require')
        return conn
    except Exception as e:
        print(f"[ERROR CRÍTICO] Fallo de conexión a Supabase: {e}")
        return None

def ejecutar_query(query, parametros=None, fetch=False):
    """Ejecuta consultas de forma segura devolviendo diccionarios."""
    conn = obtener_conexion_pg()
    if not conn: return False
    
    try:
        from psycopg2.extras import RealDictCursor
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # --- FIX DE ZONA HORARIA ---
        # Forzamos al servidor de AWS a operar en la hora de Chiapas/Centro de México
        # para esta transacción específica.
        cursor.execute("SET TIME ZONE 'America/Mexico_City';")
        # ---------------------------
        
        cursor.execute(query, parametros)
        
        if fetch:
            resultado = cursor.fetchall()
            conn.commit()
            return resultado
        
        conn.commit()
        return True
    except Exception as e:
        print(f"[ERROR SQL] {e}")
        conn.rollback()
        return str(e)
    finally:
        if 'cursor' in locals(): cursor.close()
        if conn: conn.close()