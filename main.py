import customtkinter as ctk
from tkinter import messagebox
import os
import sys
from PIL import Image
from dotenv import load_dotenv

# Vistas
from src.views.asistencia_view import AsistenciaFrame
from src.views.empleado_view import EmpleadoFrame
from src.views.nomina_view import NominaFrame
from src.views.config_view import ConfigFrame

# Controladores DB
from src.models.db_manager import ejecutar_query, inicializar_pool, cerrar_pool

# Cargamos variables de entorno
load_dotenv()

def obtener_ruta_recurso(ruta_relativa):
    """ Gestiona rutas de archivos para que funcionen en el .exe compilado """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, ruta_relativa)

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
        
        res = ejecutar_query("SELECT valor FROM config WHERE parametro = 'pin_admin'", fetch=True)
        pin_real = res[0]['valor'] if res else "1234"
        
        if pin_ingresado == pin_real: 
            self.acceso_concedido = True
            self.destroy()
        else:
            messagebox.showerror("Error", "PIN incorrecto.")
            self.ent_pin.delete(0, 'end')

# =========================================================
# CONTENEDOR PRINCIPAL V2.0
# =========================================================
class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Jesusito Pastelerías ERP - V2.0 Cloud")
        self.geometry("1100x650")
        ctk.set_appearance_mode("light")

        # --- ICONO DE VENTANA ---
        try:
            ruta_icono = obtener_ruta_recurso("assets/logo_icon.ico")
            self.iconbitmap(ruta_icono)
        except Exception as e:
            print(f"Aviso - Icono no cargado: {e}")

        # --- INICIALIZAR POOL DE BASE DE DATOS ---
        if not inicializar_pool():
            messagebox.showerror("Error de Red", "No se pudo conectar a la base de datos. Verifica tu conexión a internet.")

        # Configuración de Grid Base
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        # ==========================================
        # PANEL LATERAL (SIDEBAR) ÚNICO
        # ==========================================
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#2c3e50")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1) # Empuja elementos al fondo

        # 1. LOGO E IMAGEN
        try:
            ruta_logo = obtener_ruta_recurso("assets/logo_jesusito.png")
            mi_logo = ctk.CTkImage(light_image=Image.open(ruta_logo), size=(160, 80))
            lbl_logo = ctk.CTkLabel(self.sidebar, image=mi_logo, text="")
            lbl_logo.grid(row=0, column=0, pady=(30, 10), padx=20)
        except Exception as e:
            print(f"Aviso - Logo PNG no cargado: {e}")
            # Fallback de texto si falla la imagen
            ctk.CTkLabel(self.sidebar, text="JESUSITO\nPASTELERÍAS", font=("Helvetica", 16, "bold"), text_color="white").grid(row=0, column=0, pady=(30,10))

        # 2. TÍTULO
        self.lbl_titulo = ctk.CTkLabel(self.sidebar, text="ERP Operativo", font=("Helvetica", 16, "bold"), text_color="#bdc3c7")
        self.lbl_titulo.grid(row=1, column=0, padx=20, pady=(0, 30))

        # 3. BOTONES DE NAVEGACIÓN (Corregida duplicidad)
        self.btn_reloj = self._crear_boton_nav(2, "⏱️ Reloj Checador", self.nav_reloj)
        self.btn_personal = self._crear_boton_nav(3, "👥 Personal", self.nav_personal, protegido=True)
        self.btn_nomina = self._crear_boton_nav(4, "💰 Nómina", self.nav_nomina, protegido=True)
        self.btn_config = self._crear_boton_nav(5, "⚙️ Ajustes", self.nav_config, protegido=True)

        # 4. BOTONES Y STATUS INFERIOR
        self.btn_logout = ctk.CTkButton(self.sidebar, text="🚪 Cerrar Admin", fg_color="#c0392b", 
                                        hover_color="#a93226", font=("Helvetica", 12, "bold"),
                                        command=self.cerrar_sesion_admin)
        self.btn_logout.grid(row=6, column=0, sticky="ew", padx=20, pady=(50, 10))

        self.lbl_status = ctk.CTkLabel(self.sidebar, text="🟢 Conectado a la Nube", font=("Helvetica", 10), text_color="#2ecc71")
        self.lbl_status.grid(row=8, column=0, pady=(10, 20))

        # ==========================================
        # ÁREA DE TRABAJO PRINCIPAL
        # ==========================================
        self.main_container = ctk.CTkFrame(self, fg_color="#f0f2f5", corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        self.vista_actual = None
        self.sesion_admin_activa = False

        # Iniciar en Reloj Checador
        self.nav_reloj()

    def _crear_boton_nav(self, fila, texto, comando, protegido=False):
        cmd_final = lambda: self._rutear_acceso(comando) if protegido else comando
        
        btn = ctk.CTkButton(self.sidebar, text=texto, fg_color="transparent", text_color="#ecf0f1",
                            anchor="w", font=("Helvetica", 14, "bold"), hover_color="#34495e", 
                            height=45, command=cmd_final)
        btn.grid(row=fila, column=0, sticky="ew", padx=10, pady=5)
        return btn

    def _rutear_acceso(self, comando_destino):
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

    def cerrar_sesion_admin(self):
        self.sesion_admin_activa = False
        self.nav_reloj()
        messagebox.showinfo("Sesión Cerrada", "Has salido del modo Administrador.")

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
        self.vista_actual = ConfigFrame(self.main_container)
        self.vista_actual.pack(fill="both", expand=True, padx=20, pady=20)

    def on_closing(self):
        """Asegura un cierre limpio de la base de datos."""
        cerrar_pool()
        self.destroy()

if __name__ == "__main__":
    app = MainApp()
    # CONEXIÓN CRÍTICA: Intercepta el botón de la [X] de Windows para cerrar el Pool
    app.protocol("WM_DELETE_WINDOW", app.on_closing) 
    app.mainloop()