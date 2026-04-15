import customtkinter as ctk
from tkinter import messagebox
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from src.controllers.empleado_controller import (
    registrar_empleado, actualizar_empleado, 
    cambiar_estatus, obtener_empleados_gestion
)
from config.theme import COLOR_PRIMARIO

class EmpleadoFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="white", corner_radius=10)
        
        self.empleado_en_edicion = None # Variable pivote para saber si estamos creando o editando

        self.lbl_titulo = ctk.CTkLabel(self, text="Gestor de Personal", font=("Helvetica", 16, "bold"), text_color=COLOR_PRIMARIO)
        self.lbl_titulo.pack(pady=(10, 5))

        # --- ZONA 1: FORMULARIO ---
        self.form_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.form_frame.pack(fill="x", padx=20, pady=5)

        self.entry_nombre = ctk.CTkEntry(self.form_frame, placeholder_text="Nombre del Empleado", width=220)
        self.entry_nombre.pack(side="left", padx=5)

        self.entry_pago = ctk.CTkEntry(self.form_frame, placeholder_text="Sueldo/Hr (ej. 25)", width=130)
        self.entry_pago.pack(side="left", padx=5)

        self.btn_guardar = ctk.CTkButton(self.form_frame, text="Agregar Nuevo", width=120, fg_color=COLOR_PRIMARIO, command=self.guardar_datos)
        self.btn_guardar.pack(side="left", padx=5)

        self.btn_cancelar = ctk.CTkButton(self.form_frame, text="Cancelar", width=80, fg_color="gray", command=self.limpiar_formulario)
        # El botón cancelar no se empaqueta aún, solo aparece si estamos editando
        
        # --- ZONA 2: LISTA DE EMPLEADOS ---
        self.lista_frame = ctk.CTkScrollableFrame(self, height=180, fg_color="#F2F2F2")
        self.lista_frame.pack(fill="both", expand=True, padx=20, pady=(10, 15))

        self.cargar_lista()

    def guardar_datos(self):
        nombre = self.entry_nombre.get().strip()
        pago = self.entry_pago.get().strip()

        if not nombre or not pago:
            messagebox.showwarning("Campos Vacíos", "Ingresa el nombre y el costo por hora.")
            return

        if self.empleado_en_edicion is None:
            exito = registrar_empleado(nombre, pago)
        else:
            exito = actualizar_empleado(self.empleado_en_edicion, nombre, pago)

        if exito:
            self.limpiar_formulario()
            self.cargar_lista()
        else:
            messagebox.showerror("Error de Integridad", "Fallo al guardar. Verifica que el nombre no esté duplicado.")

    def cargar_lista(self):
        # 1. Limpiamos la lista actual
        for widget in self.lista_frame.winfo_children():
            widget.destroy()

        # 2. Obtenemos datos frescos de SQLite
        empleados = obtener_empleados_gestion()
        
        # 3. Dibujamos las filas
        for emp_id, nombre, pago, estatus in empleados:
            row_frame = ctk.CTkFrame(self.lista_frame, fg_color="white", corner_radius=5)
            row_frame.pack(fill="x", pady=2, padx=5)
            
            color_texto = "black" if estatus == "Activo" else "gray"
            lbl_info = ctk.CTkLabel(row_frame, text=f"{nombre}  |  ${pago:.2f}/hr  |  {estatus}", text_color=color_texto, font=("Helvetica", 12))
            lbl_info.pack(side="left", padx=15, pady=5)

            # Botones dinámicos según el estatus
            if estatus == "Activo":
                btn_baja = ctk.CTkButton(row_frame, text="Dar de Baja", width=80, fg_color="#dc3545", hover_color="#c82333", height=26,
                                         command=lambda i=emp_id: self.toggle_estatus(i, "Inactivo"))
                btn_baja.pack(side="right", padx=5, pady=5)
                
                btn_editar = ctk.CTkButton(row_frame, text="✏️ Editar", width=70, fg_color="#17a2b8", hover_color="#138496", height=26,
                                           command=lambda i=emp_id, n=nombre, p=pago: self.cargar_edicion(i, n, p))
                btn_editar.pack(side="right", padx=5, pady=5)
            else:
                btn_alta = ctk.CTkButton(row_frame, text="Reactivar", width=80, fg_color="#28a745", hover_color="#218838", height=26,
                                         command=lambda i=emp_id: self.toggle_estatus(i, "Activo"))
                btn_alta.pack(side="right", padx=5, pady=5)

            # --- NUEVO BOTÓN DE HISTORIAL (Aparece para activos e inactivos) ---
            btn_historial = ctk.CTkButton(row_frame, text="🕒 Historial", width=80, fg_color="#6c757d", hover_color="#5a6268", height=26,
                                          command=lambda n=nombre: self.mostrar_historial(n))
            btn_historial.pack(side="right", padx=5, pady=5)

    def cargar_edicion(self, emp_id, nombre, pago):
        """Prepara el formulario superior para modificar un registro existente."""
        self.empleado_en_edicion = emp_id
        
        self.entry_nombre.delete(0, 'end')
        self.entry_nombre.insert(0, nombre)
        
        self.entry_pago.delete(0, 'end')
        self.entry_pago.insert(0, str(pago))
        
        # Transformación visual del botón principal
        self.btn_guardar.configure(text="💾 Guardar Cambios", fg_color="#ffc107", text_color="black", hover_color="#e0a800")
        self.btn_cancelar.pack(side="left", padx=5)

    def limpiar_formulario(self):
        """Restaura el formulario a su estado original (Alta de nuevo empleado)."""
        self.empleado_en_edicion = None
        self.entry_nombre.delete(0, 'end')
        self.entry_pago.delete(0, 'end')
        
        self.btn_guardar.configure(text="Agregar Nuevo", fg_color=COLOR_PRIMARIO, text_color="white", hover_color="#155B96")
        self.btn_cancelar.pack_forget()

    def toggle_estatus(self, emp_id, nuevo_estatus):
        exito = cambiar_estatus(emp_id, nuevo_estatus)
        if exito:
            self.cargar_lista()

    def mostrar_historial(self, nombre):
        """Abre una ventana modal con el historial detallado del empleado."""
        from src.controllers.asistencia_controller import obtener_historial_empleado
        
        # Construcción del Modal
        modal = ctk.CTkToplevel(self)
        modal.title(f"Auditoría de Asistencia: {nombre}")
        modal.geometry("450x500")
        modal.transient(self.winfo_toplevel()) # Mantiene la ventana siempre al frente
        modal.grab_set() # Bloquea clics en la ventana principal hasta cerrar el modal
        
        lbl_titulo = ctk.CTkLabel(modal, text=f"Registros de {nombre}", font=("Helvetica", 16, "bold"), text_color=COLOR_PRIMARIO)
        lbl_titulo.pack(pady=15)
        
        # Contenedor desplazable para los datos
        scroll_historial = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        scroll_historial.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        registros = obtener_historial_empleado(nombre)
        
        if not registros:
            ctk.CTkLabel(scroll_historial, text="No hay movimientos registrados.", text_color="gray").pack(pady=20)
            return

        # Encabezados de tabla
        header_frame = ctk.CTkFrame(scroll_historial, fg_color=COLOR_PRIMARIO, corner_radius=0)
        header_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(header_frame, text="Fecha", width=110, text_color="white", font=("Helvetica", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Hora", width=110, text_color="white", font=("Helvetica", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Movimiento", width=110, text_color="white", font=("Helvetica", 12, "bold")).pack(side="left", padx=5)

        # Iteración de registros
        for i, (fecha, hora, tipo) in enumerate(registros):
            bg_color = "white" if i % 2 == 0 else "#F9F9F9"
            row = ctk.CTkFrame(scroll_historial, fg_color=bg_color, height=30, corner_radius=0)
            row.pack(fill="x", pady=1)
            
            # Código de color para identificación visual rápida
            color_tipo = "#28a745" if tipo == "Entrada" else "#dc3545"
            
            ctk.CTkLabel(row, text=fecha, width=110, text_color="black").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=hora, width=110, text_color="black").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=tipo, width=110, text_color=color_tipo, font=("Helvetica", 11, "bold")).pack(side="left", padx=5)