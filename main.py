import customtkinter as ctk
import os
import sys

# Rutas y Configuración
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from config.theme import COLOR_PRIMARIO, COLOR_FONDO

# Clave de acceso administrativa (Se usará si no hay una en BD)
PIN_ADMIN = "1234"

class SistemaAsistencia(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Jesusito Pastelerías - Terminal de Asistencia")
        self.geometry("1000x800")
        self.configure(fg_color=COLOR_FONDO)
        
        # 1. Contenedor Desplazable
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll_container.pack(fill="both", expand=True, padx=10, pady=10)

        # 2. Encabezado con Botón de Bloqueo
        self.header = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.header.pack(fill="x", pady=(10, 20))
        
        self.lbl_titulo = ctk.CTkLabel(self.header, text="JESUSITO PASTELERÍAS", font=("Helvetica", 28, "bold"), text_color=COLOR_PRIMARIO)
        self.lbl_titulo.pack(side="left", padx=40)

        self.btn_admin = ctk.CTkButton(self.header, text="🔒 Modo Admin", width=120, fg_color="gray", command=self.verificar_admin)
        self.btn_admin.pack(side="right", padx=40)

        # 3. Módulo de Asistencia (PÚBLICO - Siempre visible)
        # CORRECCIÓN: Se agrega el prefijo src.views para localizar el archivo
        from src.views.asistencia_view import AsistenciaFrame
        self.panel_asistencia = AsistenciaFrame(self.scroll_container)
        self.panel_asistencia.pack(pady=10, padx=40, fill="x")

        # Contenedores para módulos privados inicializados en vacío
        self.panel_empleados = None
        self.panel_reporte = None
        self.panel_gerencial = None

    def verificar_admin(self):
        # Si alguno de los paneles administrativos existe, significa que queremos SALIR
        if self.panel_empleados is not None or self.panel_reporte is not None:
            self.cerrar_sesion_admin()
            return

        # Si no, procedemos a pedir el PIN dinámico
        from src.models.db_manager import crear_conexion
        pin_real = PIN_ADMIN 
        
        conn = crear_conexion()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT valor FROM config WHERE parametro = 'pin_admin'")
                resultado = cursor.fetchone()
                if resultado: pin_real = resultado[0]
            except: pass
            finally: conn.close()

        dialogo = ctk.CTkInputDialog(text="Ingrese el PIN de Administradora:", title="Seguridad")
        try:
            password = dialogo.get_input()
        except:
            password = None

        if password == pin_real:
            self.abrir_sesion_admin()
        elif password is not None:
            from tkinter import messagebox
            messagebox.showerror("Error", "PIN Incorrecto")

    def abrir_sesion_admin(self):
        # 1. Importaciones con rutas absolutas
        from src.views.empleado_view import EmpleadoFrame
        from src.views.gerencial_view import GerencialFrame
        from src.views.report_view import ReportView 
        
        # 2. OCULTAMOS el panel de asistencia
        self.panel_asistencia.pack_forget()
        
        self.btn_admin.configure(text="🔓 Salir Admin", fg_color=COLOR_PRIMARIO)
        
        # 3. Inyectamos paneles administrativos
        self.panel_empleados = EmpleadoFrame(self.scroll_container)
        self.panel_empleados.pack(pady=10, padx=40, fill="x")
        
        self.panel_reporte = ReportView(self.scroll_container)
        self.panel_reporte.pack(pady=10, padx=40, fill="x")
        
        self.panel_gerencial = GerencialFrame(self.scroll_container)
        self.panel_gerencial.pack(pady=10, padx=40, fill="x")

    def cerrar_sesion_admin(self):
        print("[DEBUG] Cerrando sesión y limpiando estados...")
        self.btn_admin.configure(text="🔒 Modo Admin", fg_color="gray")
        
        # Destrucción física y limpieza de referencias
        if self.panel_empleados:
            self.panel_empleados.destroy()
            self.panel_empleados = None
            
        if self.panel_reporte:
            self.panel_reporte.destroy()
            self.panel_reporte = None
            
        if self.panel_gerencial:
            self.panel_gerencial.destroy()
            self.panel_gerencial = None
        
        # Refrescar y restaurar panel operativo
        self.panel_asistencia.actualizar_lista_empleados()
        self.panel_asistencia.pack(pady=10, padx=40, fill="x")

if __name__ == "__main__":
    from src.models.db_manager import inicializar_base_de_datos
    
    # 1. Verificamos o creamos la base de datos
    inicializar_base_de_datos()
    
    # 2. Arrancamos la interfaz gráfica
    # CORRECCIÓN: No se debe pasar ctk.CTk como argumento
    app = SistemaAsistencia() 
    app.mainloop()