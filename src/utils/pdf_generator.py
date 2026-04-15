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

if __name__ == "__main__":
    print("--- Generando Corte Operativo ---")
    generar_reporte_asistencia()