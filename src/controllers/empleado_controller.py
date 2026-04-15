import sqlite3
from src.models.db_manager import crear_conexion

def registrar_empleado(nombre):
    """Registra un nuevo empleado validando duplicidad y limpiando el texto."""
    nombre_limpio = nombre.strip().title() # Limpieza de datos
    
    conn = crear_conexion()
    if conn is not None:
        try:
            cursor = conn.cursor()
            sql_insert = "INSERT INTO empleados (nombre) VALUES (?)"
            cursor.execute(sql_insert, (nombre_limpio,))
            conn.commit()
            print(f"[ÉXITO] Empleado dado de alta: {nombre_limpio}")
            return True
        except sqlite3.IntegrityError:
            # Esta excepción salta automáticamente gracias a la regla UNIQUE
            print(f"[ADVERTENCIA] El empleado '{nombre_limpio}' ya está registrado.")
            return False
        except sqlite3.Error as e:
            print(f"[ERROR SQL] Fallo general de base de datos: {e}")
            return False
        finally:
            conn.close()
    return False

def obtener_empleados_activos():
    """Recupera la lista de empleados activos para el Combobox de la UI."""
    conn = crear_conexion()
    lista_empleados = []
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            sql_select = "SELECT nombre FROM empleados WHERE estatus = 'Activo' ORDER BY nombre ASC"
            cursor.execute(sql_select)
            # Extraemos los nombres de la tupla que retorna fetchall()
            lista_empleados = [fila[0] for fila in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"[ERROR SQL] No se pudo cargar el catálogo: {e}")
        finally:
            conn.close()
            
    return lista_empleados

if __name__ == "__main__":
    # Prueba de concepto (PoC)
    print("--- Inicializando PoC: Catálogo de Empleados ---")
    registrar_empleado(" María López ") # Prueba de espacios
    registrar_empleado("juan pérez")    # Prueba de mayúsculas
    registrar_empleado("María López")   # Prueba de duplicidad (IntegrityError)
    
    empleados_para_ui = obtener_empleados_activos()
    print(f"\n[DATOS PARA UI] Opciones del menú desplegable: {empleados_para_ui}")