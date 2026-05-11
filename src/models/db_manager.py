import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Variable global para el Pool de conexiones
_pool = None

def inicializar_pool():
    """Crea el túnel persistente con Supabase al arrancar la app."""
    global _pool
    uri = os.getenv("DATABASE_URL")
    if not uri:
        print("[ERROR] DATABASE_URL no encontrada.")
        return False
        
    try:
        # Creamos un pool que mantiene entre 1 y 10 conexiones abiertas y listas
        _pool = psycopg2.pool.ThreadedConnectionPool(
            1, 10, uri, sslmode='require'
        )
        print("[DB] Pool de conexiones establecido con éxito.")
        return True
    except Exception as e:
        print(f"[ERROR CRÍTICO] No se pudo crear el pool: {e}")
        return False

def ejecutar_query(query, parametros=None, fetch=False):
    """Ejecuta consultas usando el túnel abierto (instantáneo)."""
    global _pool
    
    # Si el pool no existe, intentamos crearlo
    if _pool is None:
        if not inicializar_pool(): return False
        
    conn = None
    try:
        # Pedimos una conexión prestada al pool (sin handshake, ya está abierta)
        conn = _pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Sincronía horaria con Chiapas
        cursor.execute("SET TIME ZONE 'America/Mexico_City';")
        
        cursor.execute(query, parametros)
        
        if fetch:
            resultado = cursor.fetchall()
            conn.commit()
            return resultado
        
        conn.commit()
        return True
    except Exception as e:
        if conn: conn.rollback()
        print(f"[ERROR SQL] {e}")
        return str(e)
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        # DEVOLVEMOS la conexión al pool en lugar de cerrarla
        if conn: _pool.putconn(conn)

def cerrar_pool():
    """Cierra todas las conexiones al salir de la app."""
    global _pool
    if _pool:
        _pool.closeall()
        print("[DB] Conexiones cerradas correctamente.")