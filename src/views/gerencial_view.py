import customtkinter as ctk
import os
import sys

# Rutas y configuración
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from config.theme import COLOR_PRIMARIO, COLOR_SECUNDARIO, COLOR_ACENTO
from src.utils.backup_manager import ejecutar_respaldo_total
from src.utils.pdf_generator import generar_reporte_asistencia

class GerencialFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="white", corner_radius=10)
        
        self.lbl_titulo = ctk.CTkLabel(self, text="Administración y Seguridad", font=("Helvetica", 16, "bold"), text_color=COLOR_PRIMARIO)
        self.lbl_titulo.pack(pady=15)

        # Contenedor horizontal para botones
        self.button_container = ctk.CTkFrame(self, fg_color="transparent")
        self.button_container.pack(pady=10, padx=20)

        # 1. Botón de Respaldo Cloud
        self.btn_backup = ctk.CTkButton(
            self.button_container, text="Sincronizar Nube (Drive)", 
            fg_color=COLOR_ACENTO, hover_color=COLOR_SECUNDARIO,
            command=self.accion_backup
        )
        self.btn_backup.grid(row=0, column=0, padx=10)

        # 2. Botón de Reporte PDF
        self.btn_pdf = ctk.CTkButton(
            self.button_container, text="Generar Reporte PDF", 
            fg_color=COLOR_PRIMARIO, hover_color=COLOR_SECUNDARIO,
            command=self.accion_pdf
        )
        self.btn_pdf.grid(row=0, column=1, padx=10)

        # Etiqueta de estado
        self.lbl_status = ctk.CTkLabel(self, text="Listo para acciones gerenciales", font=("Helvetica", 12))
        self.lbl_status.pack(pady=(5, 15))

    def accion_backup(self):
        self.lbl_status.configure(text="Procesando respaldo...", text_color="blue")
        if ejecutar_respaldo_total():
            self.lbl_status.configure(text="¡Respaldo local y nube completado!", text_color="green")
        else:
            self.lbl_status.configure(text="Error en respaldo. Verifique ruta de Drive.", text_color="red")

    def accion_pdf(self):
        from tkinter import filedialog
        from datetime import datetime
        
        # 1. Sugerimos un nombre por defecto
        nombre_sugerido = f"Corte_Asistencia_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        
        # 2. Abrimos la ventana de "Guardar como"
        ruta_seleccionada = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=nombre_sugerido,
            filetypes=[("Archivos PDF", "*.pdf")],
            title="Seleccione dónde guardar el reporte"
        )
        
        # 3. Si el usuario eligió una ruta (no dio cancelar)
        if ruta_seleccionada:
            self.lbl_status.configure(text="Generando y abriendo PDF...", text_color="blue")
            
            # [!] AQUÍ ESTÁ LA CORRECCIÓN: Pasamos la variable dentro del paréntesis
            if generar_reporte_asistencia(ruta_seleccionada): 
                self.lbl_status.configure(text="Reporte abierto para impresión", text_color="green")
            else:
                self.lbl_status.configure(text="Error al crear el archivo", text_color="red")
        else:
            self.lbl_status.configure(text="Operación cancelada por el usuario", text_color="orange")