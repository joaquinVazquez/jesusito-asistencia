import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from tkcalendar import DateEntry
from src.models.db_manager import ejecutar_query

class EmpleadoFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=2) 
        self.grid_rowconfigure(0, weight=1)
        
        self.empleado_actual = None 
        
        self._construir_panel_izquierdo()
        self._construir_panel_derecho()
        self.cargar_lista_empleados()

    def _construir_panel_izquierdo(self):
        frame_izq = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        frame_izq.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")
        
        ctk.CTkLabel(frame_izq, text="Directorio de Personal", font=("Helvetica", 16, "bold"), text_color="#1a1a1a").pack(pady=10)
        
        self.ent_buscador = ctk.CTkEntry(frame_izq, placeholder_text="🔍 Buscar por nombre...", fg_color="#f8f9fa", text_color="#000000")
        self.ent_buscador.pack(fill="x", padx=15, pady=5)
        self.ent_buscador.bind("<KeyRelease>", lambda event: self.cargar_lista_empleados(self.ent_buscador.get()))
        
        self.scroll_lista = ctk.CTkScrollableFrame(frame_izq, fg_color="white", corner_radius=0)
        self.scroll_lista.pack(fill="both", expand=True, padx=10, pady=10)

    def _construir_panel_derecho(self):
        self.frame_der = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        self.frame_der.grid(row=0, column=1, pady=10, sticky="nsew")
        
        self.lbl_alerta = ctk.CTkLabel(self.frame_der, text="", font=("Helvetica", 14, "bold"), text_color="white", corner_radius=5)
        
        ctk.CTkLabel(self.frame_der, text="Expediente del Empleado", font=("Helvetica", 18, "bold"), text_color="#1a1a1a").grid(row=1, column=0, columnspan=4, pady=15)
        
        self.campos = {}
        
        self.campos['nombre'] = self._crear_input(2, 0, "Nombre Completo *")
        self.campos['estatus'] = self._crear_combo(2, 2, "Estatus", ["Activo", "Inactivo"])
        self.campos['rol'] = self._crear_input(3, 0, "Rol / Puesto")
        self.campos['telefono'] = self._crear_input(3, 2, "Teléfono")
        self.campos['direccion'] = self._crear_input(4, 0, "Dirección Completa", colspan=3, width=420)
        
        # Nuevos selectores de Calendario
        self.campos['fecha_nacimiento'] = self._crear_calendario(5, 0, "Fecha Nacimiento")
        self.campos['fecha_ingreso'] = self._crear_calendario(5, 2, "Fecha Ingreso")
        
        self.campos['pago_hora'] = self._crear_input(6, 0, "Pago por Hora ($)")
        self.campos['jornada_base'] = self._crear_input(6, 2, "Jornada Base (Hrs)")
        self.campos['expediente'] = self._crear_input(7, 0, "Enlace a Expediente", colspan=3, width=420)
        
        self.lbl_antiguedad = ctk.CTkLabel(self.frame_der, text="Antigüedad: --", font=("Helvetica", 12, "italic"), text_color="#555555")
        self.lbl_antiguedad.grid(row=8, column=0, columnspan=4, pady=15)
        
        frame_acciones = ctk.CTkFrame(self.frame_der, fg_color="transparent")
        frame_acciones.grid(row=9, column=0, columnspan=4, pady=10)
        
        ctk.CTkButton(frame_acciones, text="🧹 Nuevo / Limpiar", fg_color="#6c757d", text_color="white", command=self.limpiar_formulario).pack(side="left", padx=10)
        ctk.CTkButton(frame_acciones, text="💾 Guardar Cambios", fg_color="#28a745", hover_color="#218838", text_color="white", command=self.guardar_empleado).pack(side="left", padx=10)

    def _crear_input(self, row, col, label_text, colspan=1, width=150):
        ctk.CTkLabel(self.frame_der, text=label_text, font=("Helvetica", 12, "bold"), text_color="#333333").grid(row=row, column=col, padx=10, pady=5, sticky="w")
        ent = ctk.CTkEntry(self.frame_der, width=width, fg_color="#ffffff", text_color="#000000", border_color="#cccccc")
        ent.grid(row=row, column=col+1, columnspan=colspan, padx=10, pady=5, sticky="w")
        return ent

    def _crear_combo(self, row, col, label_text, values, width=150):
        ctk.CTkLabel(self.frame_der, text=label_text, font=("Helvetica", 12, "bold"), text_color="#333333").grid(row=row, column=col, padx=10, pady=5, sticky="w")
        cmb = ctk.CTkOptionMenu(self.frame_der, values=values, width=width, fg_color="#ffffff", text_color="#000000", button_color="#e0e0e0", button_hover_color="#cccccc")
        cmb.grid(row=row, column=col+1, padx=10, pady=5, sticky="w")
        return cmb

    def _crear_calendario(self, row, col, label_text):
        ctk.CTkLabel(self.frame_der, text=label_text, font=("Helvetica", 12, "bold"), text_color="#333333").grid(row=row, column=col, padx=10, pady=5, sticky="w")
        # Selector visual con formato de base de datos
        cal = DateEntry(self.frame_der, width=18, background='#2c3e50', foreground='white', 
                        borderwidth=2, date_pattern='yyyy-mm-dd', state="readonly")
        cal.grid(row=row, column=col+1, padx=10, pady=5, sticky="w")
        cal.delete(0, 'end') # Lo dejamos en blanco por defecto
        return cal

    def cargar_lista_empleados(self, filtro=""):
        for widget in self.scroll_lista.winfo_children():
            widget.destroy()
            
        query = "SELECT nombre, rol FROM empleados WHERE nombre ILIKE %s ORDER BY nombre"
        filas = ejecutar_query(query, (f"%{filtro}%",), fetch=True)
        
        if not filas: return

        for row in filas:
            nombre = row['nombre']
            rol_txt = row['rol'] if row['rol'] else "General"
            
            btn = ctk.CTkButton(self.scroll_lista, text=f"{nombre}\n({rol_txt})", 
                                fg_color="#f8f9fa", text_color="#000000", hover_color="#e2e6ea",
                                corner_radius=0, border_spacing=5,
                                anchor="w", command=lambda n=nombre: self.seleccionar_empleado(n))
            btn.pack(fill="x", pady=2)

    def seleccionar_empleado(self, nombre):
        query = "SELECT * FROM empleados WHERE nombre = %s"
        filas = ejecutar_query(query, (nombre,), fetch=True)
        
        if filas:
            row = filas[0]
            self.limpiar_formulario()
            self.empleado_actual = row['nombre']
            
            self.campos['nombre'].insert(0, row['nombre'] or "")
            self.campos['nombre'].configure(state="disabled") 
            self.campos['telefono'].insert(0, row['telefono'] or "")
            self.campos['rol'].insert(0, row['rol'] or "")
            self.campos['direccion'].insert(0, row['direccion'] or "")
            
            # Inyección de fechas en el calendario
            if row['fecha_nacimiento']:
                self.campos['fecha_nacimiento'].set_date(row['fecha_nacimiento'])
            if row['fecha_ingreso']:
                self.campos['fecha_ingreso'].set_date(row['fecha_ingreso'])
            
            self.campos['expediente'].insert(0, row['expediente'] or "")
            self.campos['pago_hora'].insert(0, str(row['pago_hora'] if row['pago_hora'] is not None else ""))
            self.campos['jornada_base'].insert(0, str(row['jornada_base'] if row['jornada_base'] is not None else ""))
            self.campos['estatus'].set(row['estatus'] or "Activo")
            
            fnac = row['fecha_nacimiento'].strftime("%Y-%m-%d") if row['fecha_nacimiento'] else ""
            fing = row['fecha_ingreso'].strftime("%Y-%m-%d") if row['fecha_ingreso'] else ""
            self.motor_fechas_y_alertas(fnac, fing)

    def motor_fechas_y_alertas(self, nacimiento, ingreso):
        self.lbl_alerta.grid_forget()
        hoy = datetime.now()
        
        if nacimiento:
            try:
                fn = datetime.strptime(nacimiento, "%Y-%m-%d")
                if fn.month == hoy.month and fn.day == hoy.day:
                    self.lbl_alerta.configure(text="🎉 ¡HOY ES SU CUMPLEAÑOS! 🎉", fg_color="#ffc107", text_color="black")
                    self.lbl_alerta.grid(row=0, column=0, columnspan=4, pady=(0, 10), sticky="ew", padx=20)
            except: pass
            
        if ingreso:
            try:
                fi = datetime.strptime(ingreso, "%Y-%m-%d")
                anos = hoy.year - fi.year
                meses = hoy.month - fi.month
                if hoy.day < fi.day: meses -= 1
                if meses < 0:
                    anos -= 1
                    meses += 12
                self.lbl_antiguedad.configure(text=f"Antigüedad: {anos} años, {meses} meses")
            except:
                self.lbl_antiguedad.configure(text="Antigüedad: Error de cálculo")

    def guardar_empleado(self):
        datos = {k: v.get() for k, v in self.campos.items()}
        if not datos['nombre']:
            messagebox.showwarning("Auditoría", "El nombre es un campo obligatorio.")
            return
            
        try:
            pago = float(datos['pago_hora']) if datos['pago_hora'] else 0.0
            jornada = int(datos['jornada_base']) if datos['jornada_base'] else 8
            
            # Captura segura de los calendarios (vacíos o con fecha)
            f_nac = datos['fecha_nacimiento'] if datos['fecha_nacimiento'] else None
            f_ing = datos['fecha_ingreso'] if datos['fecha_ingreso'] else None
            
            if self.empleado_actual:
                query = """
                    UPDATE empleados SET 
                    telefono=%s, rol=%s, direccion=%s, fecha_nacimiento=%s, 
                    fecha_ingreso=%s, expediente=%s, pago_hora=%s, jornada_base=%s, estatus=%s
                    WHERE nombre=%s
                """
                params = (datos['telefono'], datos['rol'], datos['direccion'], f_nac, f_ing, 
                          datos['expediente'], pago, jornada, datos['estatus'], self.empleado_actual)
            else:
                query = """
                    INSERT INTO empleados (nombre, telefono, rol, direccion, fecha_nacimiento, fecha_ingreso, expediente, pago_hora, jornada_base, estatus)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (datos['nombre'], datos['telefono'], datos['rol'], datos['direccion'], f_nac, 
                          f_ing, datos['expediente'], pago, jornada, datos['estatus'])
            
            exito = ejecutar_query(query, params)
            
            if exito is True:
                messagebox.showinfo("Transacción", "Expediente procesado en PostgreSQL correctamente.")
                self.cargar_lista_empleados()
                self.limpiar_formulario()
            else:
                messagebox.showerror("Error SQL", f"Fallo en la transacción:\n{exito}")
                
        except ValueError:
            messagebox.showerror("Validación", "Los campos 'Pago' y 'Jornada' deben ser números.")

    def limpiar_formulario(self):
        self.empleado_actual = None
        self.lbl_alerta.grid_forget()
        self.lbl_antiguedad.configure(text="Antigüedad: --")
        
        self.campos['nombre'].configure(state="normal")
        for k, v in self.campos.items():
            if isinstance(v, ctk.CTkEntry):
                v.delete(0, 'end')
            elif k in ['fecha_nacimiento', 'fecha_ingreso']:
                v.delete(0, 'end') # Limpia el calendario
        self.campos['estatus'].set("Activo")