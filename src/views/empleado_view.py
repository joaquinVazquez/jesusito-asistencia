import customtkinter as ctk
import os
import sys

# Apuntamos a la raíz para importar la configuración y controladores
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from config.theme import COLOR_PRIMARIO, COLOR_SECUNDARIO
from src.controllers.empleado_controller import registrar_empleado

class EmpleadoFrame(ctk.CTkFrame):
    def __init__(self, master):
        # Creamos la caja con fondo blanco y bordes redondeados para que resalte
        super().__init__(master, fg_color="white", corner_radius=10)
        
        # 1. Título del Panel
        self.lbl_titulo = ctk.CTkLabel(self, text="Alta de Nuevo Empleado", font=("Helvetica", 16, "bold"), text_color=COLOR_PRIMARIO)
        self.lbl_titulo.pack(pady=(15, 5))
        
        # 2. Campo de Texto (Input)
        self.entry_nombre = ctk.CTkEntry(self, placeholder_text="Ej. Pedro Mostrador", width=250)
        self.entry_pago = ctk.CTkEntry(self, placeholder_text="Costo por Hora (ej. 62.5)", width=250)
        self.entry_pago.pack(pady=10)
        self.entry_pago = ctk.CTkEntry(self, placeholder_text="Costo por Hora (ej. 62.5)", width=250)
        self.entry_pago.pack(pady=10)
        self.entry_nombre.pack(pady=10)
        
        # 3. Botón de Acción
        self.btn_guardar = ctk.CTkButton(
            self, text="Registrar", 
            fg_color=COLOR_PRIMARIO, hover_color=COLOR_SECUNDARIO, 
            command=self.guardar_datos
        )
        self.btn_guardar.pack(pady=10)
        
        # 4. Etiqueta de Respuesta (UX)
        self.lbl_mensaje = ctk.CTkLabel(self, text="", font=("Helvetica", 12))
        self.lbl_mensaje.pack(pady=(0, 10))

    def guardar_datos(self):
        """Captura el texto de la UI y lo envía al backend SQLite."""
        nombre = self.entry_nombre.get()
        pago = self.entry_pago.get()
        
        if nombre.strip() == "":
            self.lbl_mensaje.configure(text="El nombre no puede estar vacío.", text_color="red")
            return
            
        exito = registrar_empleado(nombre. pago)
        
        if exito:
            self.lbl_mensaje.configure(text=f"¡'{nombre}' registrado exitosamente!", text_color="green")
            self.entry_nombre.delete(0, 'end') # Limpia el campo para el siguiente
        else:
            self.lbl_mensaje.configure(text="El empleado ya existe o hubo un error.", text_color="red")