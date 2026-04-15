import customtkinter as ctk
from tkinter import messagebox
import os
import shutil
from datetime import datetime

class GerencialFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="white", corner_radius=10)
        
        self.lbl_titulo = ctk.CTkLabel(self, text="Mantenimiento del Sistema", font=("Helvetica", 16, "bold"))
        self.lbl_titulo.pack(pady=10)

        # Único botón necesario aquí, el PDF ya se maneja en ReportView
        self.btn_backup = ctk.CTkButton(self, text="💾 Respaldar Base de Datos", width=220, command=self.accion_backup)
        self.btn_backup.pack(pady=15)
        
        self.lbl_status = ctk.CTkLabel(self, text="", text_color="gray")
        self.lbl_status.pack(pady=5)

    def accion_backup(self):
        """Genera una copia de seguridad segura de la base de datos."""
        from tkinter import filedialog
        ruta_destino = filedialog.askdirectory(title="Seleccionar carpeta para el respaldo")
        
        if ruta_destino:
            try:
                # Rutas absolutas para evitar fallos de ubicación
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                db_origen = os.path.join(BASE_DIR, "data", "jesusito_asistencia.db")
                
                fecha = datetime.now().strftime("%Y%m%d_%H%M")
                db_destino = os.path.join(ruta_destino, f"respaldo_BD_Jesusito_{fecha}.db")
                
                # Copia profunda del archivo SQLite
                shutil.copy2(db_origen, db_destino)
                
                self.lbl_status.configure(text="Respaldo completado", text_color="green")
                messagebox.showinfo("Respaldo Exitoso", f"Copia de seguridad guardada en:\n{db_destino}")
            except Exception as e:
                self.lbl_status.configure(text="Error de lectura/escritura", text_color="red")
                messagebox.showerror("Error Crítico", f"No se pudo completar el respaldo:\n{e}")