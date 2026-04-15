import customtkinter as ctk
import os
import sys
from datetime import datetime

# Rutas y configuración
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from config.theme import COLOR_PRIMARIO, COLOR_SECUNDARIO
from src.controllers.empleado_controller import obtener_empleados_activos
from src.controllers.asistencia_controller import registrar_asistencia

class AsistenciaFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="white", corner_radius=10)
        
        self.lbl_titulo = ctk.CTkLabel(self, text="Registro Operativo de Asistencia", font=("Helvetica", 16, "bold"), text_color=COLOR_PRIMARIO)
        self.lbl_titulo.grid(row=0, column=0, columnspan=2, pady=(15, 15))

        # 1. Combobox de Empleados (Conectado a SQLite)
        self.lbl_emp = ctk.CTkLabel(self, text="Empleado:", text_color="black", font=("Helvetica", 12, "bold"))
        self.lbl_emp.grid(row=1, column=0, padx=20, pady=5, sticky="e")
        
        empleados_activos = obtener_empleados_activos()
        if not empleados_activos:
            empleados_activos = ["Sin empleados registrados"]
            
        self.cmb_empleado = ctk.CTkComboBox(self, values=empleados_activos, width=200, command=self.al_seleccionar_empleado)
        self.cmb_empleado.grid(row=1, column=1, padx=20, pady=5, sticky="w")

        # 2. Entrada de Fecha (Autocompletada)
        self.lbl_fecha = ctk.CTkLabel(self, text="Fecha (YYYY-MM-DD):", text_color="black")
        self.lbl_fecha.grid(row=2, column=0, padx=20, pady=5, sticky="e")
        
        self.entry_fecha = ctk.CTkEntry(self, width=200)
        self.entry_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_fecha.grid(row=2, column=1, padx=20, pady=5, sticky="w")

        # 3. Entrada de Hora (Bloqueada)
        self.lbl_hora = ctk.CTkLabel(self, text="Hora de Registro:", text_color="black")
        self.lbl_hora.grid(row=3, column=0, padx=20, pady=5, sticky="e")
        
        # Usamos state="readonly" para que no se pueda escribir, pero el sistema pueda leerlo
        self.entry_hora = ctk.CTkEntry(self, width=200, state="readonly")
        self.entry_hora.grid(row=3, column=1, padx=20, pady=5, sticky="w")
        
        # Función para actualizar la hora en tiempo real
        self.actualizar_reloj()

        # 4. Combobox de Tipo de Registro
        self.lbl_tipo = ctk.CTkLabel(self, text="Acción:", text_color="black", font=("Helvetica", 12, "bold"))
        self.lbl_tipo.grid(row=4, column=0, padx=20, pady=5, sticky="e")
        
        self.cmb_tipo = ctk.CTkComboBox(self, values=["Entrada", "Salida", "Falta Justificada"], width=200)
        self.cmb_tipo.grid(row=4, column=1, padx=20, pady=5, sticky="w")

        # 5. Botón de Acción
        self.btn_registrar = ctk.CTkButton(
            self, text="Guardar Registro", 
            fg_color=COLOR_PRIMARIO, hover_color=COLOR_SECUNDARIO, 
            command=self.procesar_asistencia
        )
        self.btn_registrar.grid(row=5, column=0, columnspan=2, pady=20)

        # 6. Etiqueta de Respuesta (UX)
        self.lbl_mensaje = ctk.CTkLabel(self, text="", font=("Helvetica", 12))
        self.lbl_mensaje.grid(row=6, column=0, columnspan=2, pady=(0, 10))

    def procesar_asistencia(self):
        """Envía los datos validados al controlador del backend."""
        emp = self.cmb_empleado.get()
        fecha = self.entry_fecha.get()
        hora = self.entry_hora.get()
        tipo = self.cmb_tipo.get()

        if emp == "Sin empleados registrados" or not emp:
            self.lbl_mensaje.configure(text="Error: Selecciona un empleado válido.", text_color="red")
            return

        exito = registrar_asistencia(emp, fecha, hora, tipo)
        
        if exito:
            self.lbl_mensaje.configure(text=f"¡{tipo} de {emp} registrada con éxito!", text_color="green")
            # Refrescamos la hora para el siguiente empleado
            self.entry_hora.delete(0, 'end')
            self.entry_hora.insert(0, datetime.now().strftime("%H:%M"))
        else:
            self.lbl_mensaje.configure(text="Fallo de base de datos. Revisa los logs.", text_color="red")

    def actualizar_reloj(self):
        hora_actual = datetime.now().strftime("%H:%M:%S")
        self.entry_hora.configure(state="normal")
        self.entry_hora.delete(0, 'end')
        self.entry_hora.insert(0, hora_actual)
        self.entry_hora.configure(state="readonly")
        self.after(1000, self.actualizar_reloj) # Actualiza cada segundo
    
    # def actualizar_reloj(self):
    #     """Mantiene la hora actualizada cada segundo y la inyecta en el campo."""
    #     hora_actual = datetime.now().strftime("%H:%M:%S")
    #     self.entry_hora.configure(state="normal") # Desbloqueo temporal para escribir
    #     self.entry_hora.delete(0, 'end')
    #     self.entry_hora.insert(0, hora_actual)
    #     self.entry_hora.configure(state="readonly") # Bloqueo permanente para el usuario
    #     self.after(1000, self.actualizar_reloj) # Se llama a sí misma cada segundo
    #     self.entry_hora = ctk.CTkEntry(self, width=200, state="readonly") # Bloqueado
    #     self.entry_hora.grid(row=3, column=1, padx=20, pady=5, sticky="w")
    #     self.actualizar_reloj()

    def actualizar_lista_empleados(self):
        """Consulta la base de datos y refresca el ComboBox."""
        from src.controllers.empleado_controller import obtener_empleados_activos
        empleados_activos = obtener_empleados_activos()
        
        # Actualizamos los valores del ComboBox
        self.cmb_empleado.configure(values=empleados_activos)
        
        # Si la lista está vacía, limpiamos el texto actual
        if not empleados_activos:
            self.cmb_empleado.set("")
        elif self.cmb_empleado.get() not in empleados_activos:
            self.cmb_empleado.set(empleados_activos[0])

    
    def al_seleccionar_empleado(self, nombre_seleccionado):
        """Bloquea dinámicamente las opciones de Entrada/Salida según el historial."""
        from src.controllers.asistencia_controller import obtener_ultimo_estado_hoy
        
        ultimo_estado = obtener_ultimo_estado_hoy(nombre_seleccionado)
        
        if ultimo_estado == "Entrada":
            self.cmb_tipo.configure(values=["Salida"])
            self.cmb_tipo.set("Salida")
            mensaje = f"{nombre_seleccionado} tiene turno Activo. Siguiente acción: Salida."
        else:
            self.cmb_tipo.configure(values=["Entrada"])
            self.cmb_tipo.set("Entrada")
            mensaje = f"{nombre_seleccionado} está fuera. Siguiente acción: Entrada."
            
        # Candado de seguridad: Solo actualiza el texto si el widget ya cargó en memoria
        if hasattr(self, 'lbl_status'):
            self.lbl_status.configure(text=mensaje, text_color="blue")
    
    def guardar_registro(self):
        empleado = self.cmb_empleado.get()
        fecha = self.entry_fecha.get()
        hora = self.entry_hora.get() # Será ignorada por el controlador por seguridad
        tipo = self.cmb_tipo.get()

        if not empleado or not fecha or not hora or not tipo:
            self.lbl_status.configure(text="Error: Todos los campos son obligatorios", text_color="red")
            return

        from src.controllers.asistencia_controller import registrar_asistencia
        
        # Capturamos la tupla (estado, mensaje)
        exito, mensaje = registrar_asistencia(empleado, fecha, hora, tipo)

        if exito:
            self.lbl_status.configure(text=f"Éxito: {tipo} de {empleado} registrada", text_color="green")
            # Reseteamos el selector de tipo para el siguiente empleado
            self.cmb_tipo.set("Entrada")
            self.cmb_empleado.set("")
        else:
            from tkinter import messagebox
            self.lbl_status.configure(text="Registro bloqueado", text_color="orange")
            # Mostramos el motivo exacto del bloqueo en una ventana emergente
            messagebox.showwarning("Advertencia de Seguridad", mensaje)