import os
import sys
from datetime import datetime
from fpdf import FPDF

# Rutas del sistema
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PDF_DIR = os.path.join(BASE_DIR, "backups", "reports_pdf")

# Importaciones locales
sys.path.append(BASE_DIR)
from src.models.db_manager import crear_conexion

def generar_reporte_asistencia(ruta_destino): # Ahora recibe la ruta elegida por el usuario
    """Extrae datos de SQLite y construye el PDF en la ruta especificada."""
    conn = crear_conexion()
    datos = []
    if conn is not None:
        try:
            cursor = conn.cursor()
            sql_query = "SELECT empleado_nombre, fecha, hora, tipo_registro FROM asistencia ORDER BY fecha DESC, hora DESC"
            cursor.execute(sql_query)
            datos = cursor.fetchall()
        finally:
            conn.close()

    if not datos:
        return False

    pdf = FPDF(orientation="P", unit="mm", format="Letter")
    pdf.add_page()
    
    # --- (El resto del código de diseño de la tabla se mantiene igual) ---
    pdf.set_font("helvetica", "B", 20)
    pdf.set_text_color(86, 1, 22)
    pdf.cell(0, 10, "JESUSITO PASTELERIAS", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # ... (Encabezados y filas igual que antes) ...
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(220, 168, 100)
    pdf.cell(70, 8, "Empleado", border=1, fill=True)
    pdf.cell(35, 8, "Fecha", border=1, fill=True)
    pdf.cell(25, 8, "Hora", border=1, fill=True)
    pdf.cell(40, 8, "Tipo", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "", 10)
    for fila in datos:
        pdf.cell(70, 8, str(fila[0]), border=1)
        pdf.cell(35, 8, str(fila[1]), border=1, align="C")
        pdf.cell(25, 8, str(fila[2]), border=1, align="C")
        pdf.cell(40, 8, str(fila[3]), border=1, align="C", new_x="LMARGIN", new_y="NEXT")

    try:
        pdf.output(ruta_destino)
        # ESTA ES LA CLAVE: Abre el archivo automáticamente en Windows
        os.startfile(ruta_destino) 
        return True
    except Exception as e:
        print(f"[ERROR PDF] {e}")
        return False
    
from datetime import datetime

def calcular_horas(entrada, salida):
    """Calcula la diferencia de horas entre dos strings (HH:MM)."""
    fmt = '%H:%M'
    tdelta = datetime.strptime(salida, fmt) - datetime.strptime(entrada, fmt)
    return tdelta.total_seconds() / 3600 # Retorna horas en decimal (ej. 7.5)

# En la función generar_reporte_asistencia, cambia la consulta SQL:
# SELECT e.nombre, a.fecha, a.hora, a.tipo_registro, e.pago_hora 
# FROM asistencia a JOIN empleados e ON a.empleado_nombre = e.nombre    

def generar_reporte_semanal_pdf(ruta_destino):
    pdf = FPDF(orientation="L", unit="mm", format="Letter") # L = Landscape (Horizontal)
    pdf.add_page()
    
    # Configuración de fuente pequeña para que quepan 10 columnas
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(220, 168, 100) # Dorado
    
    columnas = ["Personal", "Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom", "Hrs Tot", "Salario"]
    anchos = [40, 22, 22, 22, 22, 22, 22, 22, 22, 25]

    for i, col in enumerate(columnas):
        pdf.cell(anchos[i], 8, col, border=1, fill=True, align="C")
    pdf.ln()

    # LÓGICA DE PROCESAMIENTO:
    # 1. Consultamos asistencia y empleados (JOIN)
    # 2. Iteramos por empleado
    # 3. Buscamos registros de cada día de la semana actual
    # 4. Calculamos Horas Totales * pago_hora

if __name__ == "__main__":
    print("--- Generando Corte Operativo ---")
    generar_reporte_asistencia()