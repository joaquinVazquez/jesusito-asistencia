import os
import psycopg2
import streamlit as st
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# Cargar variables de entorno
load_dotenv()

def obtener_credencial(clave):
    """
    Resuelve la credencial evaluando primero el entorno de producción (Secrets)
    y haciendo fallback al entorno local (.env).
    """
    try:
        return st.secrets[clave]
    except (FileNotFoundError, KeyError):
        return os.getenv(clave)

def get_db_connection():
    # Invocamos la función de resolución híbrida
    db_url = obtener_credencial("SUPABASE_URL")
    
    if not db_url:
        st.error("❌ ERROR CRÍTICO: No se encontró la credencial SUPABASE_URL.")
        return None

    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        st.error(f"❌ Error de conexión a infraestructura: {e}")
        return None

def ejecutar_query(query, parametros=None, fetch=False):
    conn = get_db_connection()
    if not conn:
        return []  # Retorno estandarizado a lista vacía
        
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
        st.error(f"Error SQL de ejecución: {e}")
        return []  # Retorno estandarizado a lista vacía
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()