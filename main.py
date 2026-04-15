import customtkinter as ctk
import os
import sys

# 1. Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from config.theme import COLOR_PRIMARIO, COLOR_FONDO

class SistemaAsistencia(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuración de Ventana
        self.title("Jesusito Pastelerías - Control Operativo")
        self.geometry("1000x800") # Aumentamos el tamaño base para comodidad en PC
        self.configure(fg_color=COLOR_FONDO)
        
        # 2. Contenedor Desplazable Principal
        # Eliminamos el label_text para ganar espacio limpio
        self.scroll_container = ctk.CTkScrollableFrame(
            self, 
            fg_color="transparent",
            corner_radius=0
        )
        self.scroll_container.pack(fill="both", expand=True, padx=10, pady=10)

        # 3. Título Principal (Dentro del scroll)
        self.lbl_titulo = ctk.CTkLabel(
            self.scroll_container, 
            text="JESUSITO PASTELERÍAS", 
            font=("Helvetica", 32, "bold"),
            text_color=COLOR_PRIMARIO 
        )
        self.lbl_titulo.pack(pady=(20, 30))
        
        # 4. Inyección de Módulos
        from src.views.empleado_view import EmpleadoFrame
        from src.views.asistencia_view import AsistenciaFrame
        
        # Panel 1: Empleados
        self.panel_empleados = EmpleadoFrame(self.scroll_container)
        self.panel_empleados.pack(pady=10, padx=40, fill="x", expand=False)

        # Panel 2: Asistencia
        self.panel_asistencia = AsistenciaFrame(self.scroll_container)
        self.panel_asistencia.pack(pady=10, padx=40, fill="x", expand=False)

        # --- INICIO DEL NUEVO CÓDIGO - panel gerencia ---
        from src.views.gerencial_view import GerencialFrame
        self.panel_gerencial = GerencialFrame(self.scroll_container)
        self.panel_gerencial.pack(pady=10, padx=40, fill="x", expand=False)
        # --- FIN DEL NUEVO CÓDIGO ---
        
        # 5. ESPACIADOR TÉCNICO (UX)
        # Esto genera un vacío al final para que el scroll siempre permita bajar 
        # más allá del último botón, evitando que el contenido se corte.
        self.spacer = ctk.CTkLabel(self.scroll_container, text="", height=50)
        self.spacer.pack()

        # 6. Footer fijo (Fuera del scroll)
        self.lbl_estado = ctk.CTkLabel(
            self, 
            text="Panel de Control Activo | Use la rueda del mouse para desplazar", 
            font=("Helvetica", 11, "italic"),
            text_color=COLOR_PRIMARIO
        )
        self.lbl_estado.pack(side="bottom", pady=5)

if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    app = SistemaAsistencia()
    app.mainloop()