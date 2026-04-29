import psycopg2
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def inyectar_esquema_nube():
    uri = os.getenv("DATABASE_URL")
    if not uri:
        print("[ERROR] DATABASE_URL no encontrada en .env")
        return

    print("Iniciando inyección de esquema V2.0 en Supabase...")
    
    try:
        # Conexión forzando SSL
        conn = psycopg2.connect(uri, sslmode='require')
        cursor = conn.cursor()

        # 1. Catálogo de Sucursales
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sucursales (
                id SERIAL PRIMARY KEY,
                nombre TEXT UNIQUE NOT NULL,
                ubicacion TEXT
            );
        """)

        # 2. Maestro de Empleados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empleados (
                id SERIAL PRIMARY KEY,
                nombre TEXT UNIQUE NOT NULL,
                telefono TEXT DEFAULT 'Sin registro',
                rol TEXT DEFAULT 'General',
                direccion TEXT DEFAULT 'Sin registro',
                fecha_nacimiento DATE,
                fecha_ingreso DATE,
                expediente TEXT DEFAULT '',
                pago_hora REAL DEFAULT 0.0,
                jornada_base INTEGER DEFAULT 8, 
                estatus TEXT DEFAULT 'Activo'
            );
        """)

        # 3. Registro de Asistencia (TIMESTAMPTZ para turnos nocturnos)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asistencia (
                id SERIAL PRIMARY KEY,
                empleado_id INTEGER REFERENCES empleados(id) ON DELETE CASCADE,
                sucursal_id INTEGER REFERENCES sucursales(id),
                entrada TIMESTAMPTZ,
                salida TIMESTAMPTZ,
                tipo_registro TEXT,
                observaciones TEXT
            );
        """)

        # 4. Registro de "Bases" y Comisiones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comisiones (
                id SERIAL PRIMARY KEY,
                empleado_id INTEGER REFERENCES empleados(id) ON DELETE CASCADE,
                fecha DATE DEFAULT CURRENT_DATE,
                tipo_comision TEXT,
                capacidad_base INTEGER,
                monto REAL NOT NULL,
                descripcion TEXT
            );
        """)

        # 5. Ajustes Manuales (Bonos/Descuentos)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ajustes (
                id SERIAL PRIMARY KEY,
                empleado_id INTEGER REFERENCES empleados(id) ON DELETE CASCADE,
                fecha DATE DEFAULT CURRENT_DATE,
                monto REAL NOT NULL,
                tipo TEXT,
                motivo TEXT
            );
        """)

        # 6. Tabla Configuración de Sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                parametro TEXT PRIMARY KEY, 
                valor TEXT
            );
        """)

        # --- SEEDING (Datos por Defecto) ---
        print("Inyectando catálogos por defecto...")
        
        # Sucursales (Matriz y Teopisca)
        cursor.execute("INSERT INTO sucursales (nombre, ubicacion) VALUES ('Matriz', 'Principal') ON CONFLICT DO NOTHING;")
        cursor.execute("INSERT INTO sucursales (nombre, ubicacion) VALUES ('Teopisca', 'Teopisca, Chiapas') ON CONFLICT DO NOTHING;")
        
        # PIN de Admin
        cursor.execute("INSERT INTO config (parametro, valor) VALUES ('pin_admin', '1234') ON CONFLICT DO NOTHING;")

        conn.commit()
        print("[ÉXITO] Esquema relacional implementado en PostgreSQL correctamente.")
        
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[ERROR CRÍTICO] Falló la inyección del esquema: {e}")

if __name__ == "__main__":
    inyectar_esquema_nube()