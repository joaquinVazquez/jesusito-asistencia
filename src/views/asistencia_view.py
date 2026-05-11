import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import threading  # <-- LIBRERÍA CLAVE INYECTADA PARA EVITAR CONGELAMIENTOS
from src.models.db_manager import ejecutar_query

class AsistenciaFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="white", corner_radius=10)
        
        self.mapa_empleados = {}
        self.mapa_sucursales = {}
        
        self._construir_interfaz()
        self._cargar_catalogos() # Ahora es asíncrono
        self._actualizar_reloj_local()

    def _construir_interfaz(self):
        # Reloj Digital
        self.lbl_reloj = ctk.CTkLabel(self, text="00:00:00", font=("Helvetica", 65, "bold"), text_color="#2c3e50")
        self.lbl_reloj.pack(pady=(40, 5))
        
        self.lbl_fecha = ctk.CTkLabel(self, text="Cargando fecha...", font=("Helvetica", 18), text_color="#7f8c8d")
        self.lbl_fecha.pack(pady=(0, 30))

        # Formularios
        frame_form = ctk.CTkFrame(self, fg_color="#f8f9fa", corner_radius=15)
        frame_form.pack(padx=20, pady=10, fill="x", expand=False)

        ctk.CTkLabel(frame_form, text="Ubicación de la Terminal:", font=("Helvetica", 12, "bold")).pack(pady=(15, 0))
        self.cmb_sucursal = ctk.CTkOptionMenu(frame_form, values=["Cargando de la nube..."], width=300)
        self.cmb_sucursal.pack(pady=5)

        ctk.CTkLabel(frame_form, text="Selecciona tu Nombre:", font=("Helvetica", 12, "bold")).pack(pady=(15, 0))
        self.cmb_empleado = ctk.CTkOptionMenu(frame_form, values=["Cargando de la nube..."], width=300)
        self.cmb_empleado.pack(pady=5)

        # Botones
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
        if not self.winfo_exists():
            return 
        ahora = datetime.now()
        self.lbl_reloj.configure(text=ahora.strftime("%H:%M:%S"))
        self.lbl_fecha.configure(text=ahora.strftime("%A, %d de %B de %Y").capitalize())
        self.after(1000, self._actualizar_reloj_local)

    # --- ARQUITECTURA MULTI-HILO PARA RED ---

    def _cargar_catalogos(self):
        """Lanza la descarga en un hilo secundario para no congelar la UI"""
        def tarea_red():
            try:
                suc_db = ejecutar_query("SELECT id, nombre FROM sucursales ORDER BY id", fetch=True)
                emp_db = ejecutar_query("SELECT id, nombre FROM empleados WHERE estatus = 'Activo' ORDER BY nombre", fetch=True)
                # Volvemos al hilo principal de forma segura
                self.after(0, lambda: self._aplicar_catalogos(suc_db, emp_db))
            except Exception as e:
                print(f"Error de red: {e}")
                self.after(0, lambda: self.cmb_empleado.configure(values=["Error de conexión"]))

        threading.Thread(target=tarea_red, daemon=True).start()

    def _aplicar_catalogos(self, sucursales_db, empleados_db):
        """Aplica los datos a la interfaz gráfica"""
        if sucursales_db:
            self.mapa_sucursales = {s['nombre']: s['id'] for s in sucursales_db}
            nombres_sucursales = list(self.mapa_sucursales.keys())
            self.cmb_sucursal.configure(values=nombres_sucursales)
            self.cmb_sucursal.set(nombres_sucursales[0])
        
        if empleados_db:
            self.mapa_empleados = {e['nombre']: e['id'] for e in empleados_db}
            nombres_empleados = list(self.mapa_empleados.keys())
            self.cmb_empleado.configure(values=nombres_empleados)
            if nombres_empleados: self.cmb_empleado.set(nombres_empleados[0])
        else:
            self.cmb_empleado.configure(values=["No hay personal activo"])

    # --- FUNCIONES DE BOTONES CON BLOQUEO ANTI-SPAM ---

    def registrar_entrada(self):
        emp_nombre = self.cmb_empleado.get()
        suc_nombre = self.cmb_sucursal.get()
        if emp_nombre not in self.mapa_empleados: return
        
        emp_id = self.mapa_empleados[emp_nombre]
        suc_id = self.mapa_sucursales[suc_nombre]

        # 1. Bloqueamos el botón visualmente para evitar que le den doble clic
        self.btn_entrada.configure(state="disabled", text="⏳ PROCESANDO...")

        # 2. Definimos el viaje a la nube
        def tarea_red():
            q_check = "SELECT id FROM asistencia WHERE empleado_id = %s AND salida IS NULL"
            turno = ejecutar_query(q_check, (emp_id,), fetch=True)
            
            if turno:
                self.after(0, lambda: self._resolver_boton(self.btn_entrada, "✅ MARCAR ENTRADA", "Atención", f"{emp_nombre}, ya tienes turno abierto.", "warning"))
                return

            q_insert = "INSERT INTO asistencia (empleado_id, sucursal_id, entrada, tipo_registro) VALUES (%s, %s, NOW(), 'Normal')"
            exito = ejecutar_query(q_insert, (emp_id, suc_id))
            
            if exito:
                self.after(0, lambda: self._resolver_boton(self.btn_entrada, "✅ MARCAR ENTRADA", "Éxito", f"✅ Entrada en nube para {emp_nombre}.", "info"))
            else:
                self.after(0, lambda: self._resolver_boton(self.btn_entrada, "✅ MARCAR ENTRADA", "Error", "Fallo de conexión.", "error"))

        # 3. Lanzamos el hilo
        threading.Thread(target=tarea_red, daemon=True).start()

    def registrar_salida(self):
        emp_nombre = self.cmb_empleado.get()
        if emp_nombre not in self.mapa_empleados: return
        emp_id = self.mapa_empleados[emp_nombre]

        self.btn_salida.configure(state="disabled", text="⏳ PROCESANDO...")

        def tarea_red():
            q_check = "SELECT id FROM asistencia WHERE empleado_id = %s AND salida IS NULL ORDER BY entrada DESC LIMIT 1"
            turno = ejecutar_query(q_check, (emp_id,), fetch=True)
            
            if not turno:
                self.after(0, lambda: self._resolver_boton(self.btn_salida, "🛑 MARCAR SALIDA", "Error", f"{emp_nombre}, no hay turno abierto.", "error"))
                return

            q_update = "UPDATE asistencia SET salida = NOW() WHERE id = %s"
            exito = ejecutar_query(q_update, (turno[0]['id'],))
            
            if exito:
                self.after(0, lambda: self._resolver_boton(self.btn_salida, "🛑 MARCAR SALIDA", "Éxito", f"🛑 Salida en nube para {emp_nombre}.", "info"))
            else:
                self.after(0, lambda: self._resolver_boton(self.btn_salida, "🛑 MARCAR SALIDA", "Error", "Fallo de conexión.", "error"))

        threading.Thread(target=tarea_red, daemon=True).start()

    def _resolver_boton(self, boton, texto_original, titulo, msj, tipo):
        """Restaura la interfaz después de que la nube responde"""
        boton.configure(state="normal", text=texto_original)
        if tipo == "warning": messagebox.showwarning(titulo, msj)
        elif tipo == "info": messagebox.showinfo(titulo, msj)
        elif tipo == "error": messagebox.showerror(titulo, msj)