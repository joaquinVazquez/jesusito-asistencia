from fpdf import FPDF
import os

def generar_pdf_nomina(ruta, fecha_inicio, fecha_fin, datos_matriz):
    """
    Genera un PDF horizontal iterando exactamente los datos procesados en la UI.
    """
    try:
        # Orientación L = Landscape (Horizontal)
        pdf = FPDF(orientation="L", unit="mm", format="Letter")
        pdf.add_page()
        
        # Títulos
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "JESUSITO PASTELERIAS - REPORTE DE NOMINA", ln=True, align="C")
        pdf.set_font("helvetica", "I", 12)
        pdf.cell(0, 10, f"Período: {fecha_inicio} al {fecha_fin}", ln=True, align="C")
        pdf.ln(5)
        
        # Cabeceras (Ajuste de anchos para formato Carta Horizontal: 279mm aprox)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(180, 0, 0) # Color primario (Vino)
        pdf.set_text_color(255, 255, 255)
        
        headers = ["Personal", "Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom", "Hrs Tot.", "Sueldo Sem."]
        anchos = [45, 20, 20, 20, 20, 20, 20, 20, 25, 35]
        
        for i, h in enumerate(headers):
            pdf.cell(anchos[i], 10, h, border=1, fill=True, align="C")
        pdf.ln()
        
        # Dibujado de Filas
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        
        for fila in datos_matriz:
            for i, valor in enumerate(fila):
                # Alinear nombres a la izquierda, números al centro
                alineacion = "L" if i == 0 else "C"
                pdf.cell(anchos[i], 8, str(valor), border=1, align=alineacion)
            pdf.ln()
            
        pdf.output(ruta)
        
        # Auto-abrir el PDF en Windows
        if os.name == 'nt':
            os.startfile(ruta)
        return True
        
    except Exception as e:
        print(f"[ERROR PDF] Fallo en la generación: {e}")
        return False