import customtkinter as ctk
from tkinter import messagebox
import os
from dotenv import load_dotenv
from src.views.asistencia_view import AsistenciaFrame
from src.views.empleado_view import EmpleadoFrame
from src.views.nomina_view import NominaFrame


# Cargamos variables de entorno
load_dotenv()

# =========================================================
# COMPONENTE DE SEGURIDAD (MODAL PIN)
# =========================================================
class DialogoPIN(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Seguridad Requerida")
        self.geometry("300x180")
        self.resizable(False, False)
        self.acceso_concedido = False
        
        # Centrar ventana modal
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - 150
        y = master.winfo_y() + (master.winfo_height() // 2) - 90
        self.geometry(f"+{x}+{y}")

        ctk.CTkLabel(self, text="Ingrese PIN de Administrador:", font=("Helvetica", 14, "bold")).pack(pady=(25, 10))
        
        self.ent_pin = ctk.CTkEntry(self, show="*", justify="center", width=150, font=("Helvetica", 18))
        self.ent_pin.pack(pady=5)
        self.ent_pin.bind("<Return>", self.verificar)
        
        ctk.CTkButton(self, text="Desbloquear", fg_color="#28a745", hover_color="#218838", command=self.verificar).pack(pady=15)
        
        self.ent_pin.focus()
        self.grab_set()
        self.wait_window()

    def verificar(self, event=None):
        pin_ingresado = self.ent_pin.get()
        # TODO: Leer PIN real desde PostgreSQL. Por ahora hardcodeamos el default
        if pin_ingresado == "1234": 
            self.acceso_concedido = True
            self.destroy()
        else:
            messagebox.showerror("Error", "PIN Incorrecto. Acceso denegado.")
            self.ent_pin.delete(0, 'end')

# =========================================================
# VISTAS TEMPORALES (Evitan crasheos mientras migramos a PG)
# =========================================================
class VistaEnConstruccion(ctk.CTkFrame):
    def __init__(self, master, titulo):
        super().__init__(master, fg_color="white", corner_radius=10)
        ctk.CTkLabel(self, text=titulo, font=("Helvetica", 28, "bold"), text_color="#1a1a1a").pack(expand=True, pady=(100, 0))
        ctk.CTkLabel(self, text="Migrando conexión a PostgreSQL...", font=("Helvetica", 14), text_color="#666").pack(expand=True, pady=(0, 100))

# =========================================================
# CONTENEDOR PRINCIPAL V2.0
# =========================================================
class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Jesusito Pastelerías ERP - V2.0 Cloud")
        self.geometry("1100x650")
        ctk.set_appearance_mode("light")

        # Configuración de Grid Base
        self.grid_columnconfigure(1, weight=1) # El main_container se expande
        self.grid_rowconfigure(0, weight=1)

        # --- PANEL LATERAL (SIDEBAR) ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#2c3e50")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1) # Empuja versión al fondo

        # Branding
        self.logo = ctk.CTkLabel(self.sidebar, text="JESUSITO\nPASTELERÍAS", font=("Helvetica", 20, "bold"), text_color="white")
        self.logo.grid(row=0, column=0, padx=20, pady=(30, 30))

        # Botones de Navegación
        self.btn_reloj = self._crear_boton_nav(1, "⏱️ Reloj Checador", self.nav_reloj)
        self.btn_personal = self._crear_boton_nav(2, "👥 Personal", self.nav_personal, protegido=True)
        self.btn_nomina = self._crear_boton_nav(3, "💰 Nómina Interactiva", self.nav_nomina, protegido=True)
        self.btn_config = self._crear_boton_nav(4, "⚙️ Ajustes", self.nav_config, protegido=True)

        self.lbl_status = ctk.CTkLabel(self.sidebar, text="🟢 Conectado a la Nube", font=("Helvetica", 10), text_color="#2ecc71")
        self.lbl_status.grid(row=7, column=0, pady=(10, 20))

        # --- ÁREA DE TRABAJO PRINCIPAL ---
        self.main_container = ctk.CTkFrame(self, fg_color="#f0f2f5", corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        self.vista_actual = None
        self.sesion_admin_activa = False

        # Iniciar en Reloj Checador
        self.nav_reloj()

    def _crear_boton_nav(self, fila, texto, comando, protegido=False):
        # Si es protegido, le inyectamos la validación de PIN
        cmd_final = lambda: self._rutear_acceso(comando) if protegido else comando
        
        btn = ctk.CTkButton(self.sidebar, text=texto, fg_color="transparent", text_color="#ecf0f1",
                            anchor="w", font=("Helvetica", 14, "bold"), hover_color="#34495e", 
                            height=45, command=cmd_final)
        btn.grid(row=fila, column=0, sticky="ew", padx=10, pady=5)
        return btn

    def _rutear_acceso(self, comando_destino):
        """Valida si el Admin ya metió su PIN antes de cambiar de pantalla"""
        if not self.sesion_admin_activa:
            dialogo = DialogoPIN(self)
            if dialogo.acceso_concedido:
                self.sesion_admin_activa = True
                comando_destino()
        else:
            comando_destino()

    def _limpiar_contenedor(self):
        if self.vista_actual:
            self.vista_actual.destroy()

    # --- RUTAS DE NAVEGACIÓN ---
    def nav_reloj(self):
        self._limpiar_contenedor()
        self.vista_actual = AsistenciaFrame(self.main_container)
        self.vista_actual.pack(fill="both", expand=True, padx=20, pady=20)

    def nav_personal(self):
     self._limpiar_contenedor()
     self.vista_actual = EmpleadoFrame(self.main_container)
     self.vista_actual.pack(fill="both", expand=True, padx=20, pady=20)

    def nav_nomina(self):
     self._limpiar_contenedor()
     self.vista_actual = NominaFrame(self.main_container)
     self.vista_actual.pack(fill="both", expand=True, padx=20, pady=20)

    def nav_config(self):
        self._limpiar_contenedor()
        self.vista_actual = VistaEnConstruccion(self.main_container, "⚙️ Ajustes de Sistema")
        self.vista_actual.pack(fill="both", expand=True, padx=20, pady=20)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()