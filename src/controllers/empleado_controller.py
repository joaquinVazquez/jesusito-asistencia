import sqlite3
from src.models.db_manager import crear_conexion

def registrar_empleado(nombre, pago_hora=0.0):
    nombre_limpio = nombre.strip().title()
    try: pago_float = float(pago_hora)
    except ValueError: pago_float = 0.0
    
    conn = crear_conexion()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO empleados (nombre, pago_hora) VALUES (?, ?)", (nombre_limpio, pago_float))
        conn.commit()
        return True
    except sqlite3.Error: return False
    finally: conn.close()

def actualizar_empleado(emp_id, nombre, pago_hora):
    """Sobrescribe el nombre y el sueldo de un empleado existente."""
    nombre_limpio = nombre.strip().title()
    try: pago_float = float(pago_hora)
    except ValueError: pago_float = 0.0
    
    conn = crear_conexion()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE empleados SET nombre=?, pago_hora=? WHERE id=?", (nombre_limpio, pago_float, emp_id))
        conn.commit()
        return True
    except sqlite3.Error: return False
    finally: conn.close()

def cambiar_estatus(emp_id, nuevo_estatus):
    """Cambia entre 'Activo' e 'Inactivo' (Baja lógica)."""
    conn = crear_conexion()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE empleados SET estatus=? WHERE id=?", (nuevo_estatus, emp_id))
        conn.commit()
        return True
    except sqlite3.Error: return False
    finally: conn.close()

def obtener_empleados_gestion():
    """Trae a toda la plantilla para el panel de administración."""
    conn = crear_conexion()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, pago_hora, estatus FROM empleados ORDER BY estatus ASC, nombre ASC")
        return cursor.fetchall()
    except sqlite3.Error: return []
    finally: conn.close()

def obtener_empleados_activos():
    """Trae solo a los activos para el ComboBox de la vista de Asistencia (Módulo Operativo)."""
    conn = crear_conexion()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM empleados WHERE estatus='Activo' ORDER BY nombre ASC")
        return [fila[0] for fila in cursor.fetchall()]
    except sqlite3.Error: return []
    finally: conn.close()