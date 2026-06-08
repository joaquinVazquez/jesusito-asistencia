import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_db_connection():
    # Obtenemos la cadena de conexión completa
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ ERROR: No se encontró la variable DATABASE_URL en el archivo .env")
        return None

    try:
        # psycopg2 acepta la URL completa directamente
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        return None

def ejecutar_query(query, parametros=None, fetch=False):
    conn = get_db_connection()
    if not conn:
        return "Error: No se pudo establecer conexión."
        
    cursor = None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, parametros)
            
        if fetch:
            resultados = cursor.fetchall()
            return resultados
        else:
            conn.commit()
            return True
            
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print(f"Error SQL: {e}")
        return str(e)
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()