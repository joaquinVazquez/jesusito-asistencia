import customtkinter as ctk
from tkinter import messagebox
import os
import sqlite3

class GerencialFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="white", corner_radius=10)
        
        self.lbl_titulo = ctk.CTkLabel(self, text="Configuración y Mantenimiento", font=("Helvetica", 16, "bold"))
        self.lbl_titulo.pack(pady=10)

        self.btn_container = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_container.pack(pady=10)

        # Botón de Backup
        self.btn_backup = ctk.CTkButton(self.btn_container, text="💾 Respaldar Base de Datos", width=200, command=self.accion_backup)
        self.btn_backup.pack(side="left", padx=10)

        # Botón de Cambio de PIN
        self.btn_pin = ctk.CTkButton(self.btn_container, text="🔑 Cambiar PIN Admin", width=200, fg_color="#6c757d", command=self.accion_cambiar_pin)
        self.btn_pin.pack(side="left", padx=10)
        
        self.lbl_status = ctk.CTkLabel(self, text="", text_color="gray")
        self.lbl_status.pack(pady=5)

    def accion_cambiar_pin(self):
        dialogo = ctk.CTkInputDialog(text="Ingrese el NUEVO PIN (4-6 dígitos):", title="Seguridad")
        nuevo_pin = dialogo.get_input()

        if nuevo_pin and nuevo_pin.isdigit() and len(nuevo_pin) >= 4:
            from src.models.db_manager import crear_conexion
            conn = crear_conexion()
            if conn:
                try:
                    cursor = conn.cursor()
                    # ASEGURAMOS QUE LA TABLA EXISTA ANTES DE ACTUALIZAR
                    cursor.execute("CREATE TABLE IF NOT EXISTS config (parametro TEXT PRIMARY KEY, valor TEXT)")
                    cursor.execute("INSERT OR IGNORE INTO config (parametro, valor) VALUES ('pin_admin', '1234')")
                    
                    cursor.execute("UPDATE config SET valor = ? WHERE parametro = 'pin_admin'", (nuevo_pin,))
                    conn.commit()
                    messagebox.showinfo("Éxito", "PIN de administrador actualizado correctamente.")
                    self.lbl_status.configure(text="PIN actualizado", text_color="green")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo actualizar: {e}")
                finally:
                    conn.close()
        elif nuevo_pin is not None:
            messagebox.showwarning("Formato Inválido", "El PIN debe ser numérico y tener al menos 4 dígitos.")

    def accion_backup(self):
        from tkinter import filedialog
        import shutil
        from datetime import datetime
        
        ruta_destino = filedialog.askdirectory(title="Seleccionar carpeta para el respaldo")
        if ruta_destino:
            try:
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                db_origen = os.path.join(BASE_DIR, "data", "jesusito_asistencia.db")
                fecha = datetime.now().strftime("%Y%m%d_%H%M")
                db_destino = os.path.join(ruta_destino, f"respaldo_Jesusito_{fecha}.db")
                shutil.copy2(db_origen, db_destino)
                messagebox.showinfo("Éxito", "Respaldo creado.")
            except Exception as e:
                messagebox.showerror("Error", str(e))