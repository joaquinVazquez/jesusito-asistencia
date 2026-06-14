import os
import psycopg2
import streamlit as st
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def obtener_credencial(clave):
    """
    Resuelve la credencial evaluando primero el entorno de producción
    y haciendo fallback al entorno local (.env).
    """
    try:
        # Intenta extraer de los Secrets de Streamlit Cloud
        return st.secrets[clave]
    except (FileNotFoundError, KeyError):
        # Si falla (entorno local), extrae del archivo .env
        return os.getenv(clave)

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