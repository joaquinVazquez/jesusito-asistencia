import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import time
from src.models.db_manager import ejecutar_query

class AsistenciaFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="white", corner_radius=10)
        
        # Diccionarios para mapear Nombres a IDs (Requisito de bases relacionales)
        self.mapa_empleados = {}
        self.mapa_sucursales = {}
        
        self._construir_interfaz()
        self._cargar_catalogos()
        self._actualizar_reloj_local()

    def _construir_interfaz(self):
        # Reloj Digital (Visual)
        self.lbl_reloj = ctk.CTkLabel(self, text="00:00:00", font=("Helvetica", 65, "bold"), text_color="#2c3e50")
        self.lbl_reloj.pack(pady=(40, 5))
        
        self.lbl_fecha = ctk.CTkLabel(self, text="Cargando fecha...", font=("Helvetica", 18), text_color="#7f8c8d")
        self.lbl_fecha.pack(pady=(0, 30))

        # Contenedor de Formularios
        frame_form = ctk.CTkFrame(self, fg_color="#f8f9fa", corner_radius=15)
        frame_form.pack(padx=20, pady=10, fill="x", expand=False)

        # 1. Selector de Sucursal (Ubicación física de la tablet)
        ctk.CTkLabel(frame_form, text="Ubicación de la Terminal:", font=("Helvetica", 12, "bold")).pack(pady=(15, 0))
        self.cmb_sucursal = ctk.CTkOptionMenu(frame_form, values=["Cargando..."], width=300)
        self.cmb_sucursal.pack(pady=5)

        # 2. Selector de Empleado
        ctk.CTkLabel(frame_form, text="Selecciona tu Nombre:", font=("Helvetica", 12, "bold")).pack(pady=(15, 0))
        self.cmb_empleado = ctk.CTkOptionMenu(frame_form, values=["Cargando..."], width=300)
        self.cmb_empleado.pack(pady=5)

        # Botones de Acción
        frame_botones = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_botones.pack(pady=30)

        self.btn_entrada = ctk.CTkButton(frame_botones, text="✅ MARCAR ENTRADA", 
                                         font=("Helvetica", 16, "bold"), width=180, height=50, 
                                         fg_color="#28a745", hover_color="#218838", command=self.registrar_entrada)
        self.btn_entrada.pack(side="left", padx=15)

        self.btn_salida = ctk.CTkButton(frame_botones, text="🛑 MARCAR SALIDA", 
                                        font=("Helvetica", 16, "bold"), width=180, height=50, 
                                        fg_color="#dc3545", hover_color="#c82333", command=self.registrar_salida)
        self.btn_salida.pack(side="left", padx=15)

    def _actualizar_reloj_local(self):
        """Mantiene el reloj visual en movimiento (Solo visual)"""
        ahora = datetime.now()
        self.lbl_reloj.configure(text=ahora.strftime("%H:%M:%S"))
        self.lbl_fecha.configure(text=ahora.strftime("%A, %d de %B de %Y").capitalize())
        self.after(1000, self._actualizar_reloj_local)

    def _cargar_catalogos(self):
        """Descarga de la nube las sucursales y empleados activos."""
        try:
            # Cargar Sucursales
            sucursales_db = ejecutar_query("SELECT id, nombre FROM sucursales ORDER BY id", fetch=True)
            if sucursales_db:
                self.mapa_sucursales = {s['nombre']: s['id'] for s in sucursales_db}
                nombres_sucursales = list(self.mapa_sucursales.keys())
                self.cmb_sucursal.configure(values=nombres_sucursales)
                self.cmb_sucursal.set(nombres_sucursales[0]) # Default: Matriz
            
            # Cargar Empleados
            empleados_db = ejecutar_query("SELECT id, nombre FROM empleados WHERE estatus = 'Activo' ORDER BY nombre", fetch=True)
            if empleados_db:
                self.mapa_empleados = {e['nombre']: e['id'] for e in empleados_db}
                nombres_empleados = list(self.mapa_empleados.keys())
                self.cmb_empleado.configure(values=nombres_empleados)
                if nombres_empleados: self.cmb_empleado.set(nombres_empleados[0])
            else:
                self.cmb_empleado.configure(values=["No hay personal activo"])
                
        except Exception as e:
            print(f"Error cargando catálogos: {e}")
            self.cmb_empleado.configure(values=["Error de conexión"])

    def registrar_entrada(self):
        emp_nombre = self.cmb_empleado.get()
        suc_nombre = self.cmb_sucursal.get()
        
        if emp_nombre not in self.mapa_empleados: return
        
        emp_id = self.mapa_empleados[emp_nombre]
        suc_id = self.mapa_sucursales[suc_nombre]

        # REGLA: ¿Ya tiene un turno abierto (entrada sin salida)?
        query_check = "SELECT id FROM asistencia WHERE empleado_id = %s AND salida IS NULL"
        turno_abierto = ejecutar_query(query_check, (emp_id,), fetch=True)
        
        if turno_abierto:
            messagebox.showwarning("Atención", f"{emp_nombre}, ya tienes un turno abierto. Debes marcar salida primero.")
            return

        # INSERT en PostgreSQL usando la hora del servidor (NOW())
        query_insert = """
            INSERT INTO asistencia (empleado_id, sucursal_id, entrada, tipo_registro) 
            VALUES (%s, %s, NOW(), 'Normal')
        """
        exito = ejecutar_query(query_insert, (emp_id, suc_id))
        
        if exito:
            messagebox.showinfo("Registro Exitoso", f"✅ Entrada registrada en el servidor para {emp_nombre}.")
        else:
            messagebox.showerror("Error", "Error de comunicación con la nube.")

    def registrar_salida(self):
        emp_nombre = self.cmb_empleado.get()
        if emp_nombre not in self.mapa_empleados: return
        
        emp_id = self.mapa_empleados[emp_nombre]

        # REGLA: Buscar el turno abierto de este empleado
        query_check = "SELECT id FROM asistencia WHERE empleado_id = %s AND salida IS NULL ORDER BY entrada DESC LIMIT 1"
        turno_abierto = ejecutar_query(query_check, (emp_id,), fetch=True)
        
        if not turno_abierto:
            messagebox.showerror("Error", f"{emp_nombre}, no tienes un turno abierto para marcar salida.")
            return

        # UPDATE: Actualizamos la misma fila inyectando la hora del servidor en 'salida'
        registro_id = turno_abierto[0]['id']
        query_update = "UPDATE asistencia SET salida = NOW() WHERE id = %s"
        exito = ejecutar_query(query_update, (registro_id,))
        
        if exito:
            messagebox.showinfo("Registro Exitoso", f"🛑 Salida registrada en el servidor para {emp_nombre}.")
        else:
            messagebox.showerror("Error", "Error de comunicación con la nube.")