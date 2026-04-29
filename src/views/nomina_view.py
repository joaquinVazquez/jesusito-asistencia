import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry
from src.models.db_manager import ejecutar_query
from src.controllers.nomina_controller import NominaController

# =========================================================
# MODAL DE AUDITORÍA Y COMISIONES (EL EDITOR)
# =========================================================
class EditorAuditoriaModal(ctk.CTkToplevel):
    def __init__(self, master, emp_id, nombre, fecha_inicio, fecha_fin, callback_refresh):
        super().__init__(master)
        self.title(f"Auditoría: {nombre}")
        self.geometry("700x550")
        self.emp_id = emp_id
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.callback_refresh = callback_refresh
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text=f"Editando periodo: {fecha_inicio} al {fecha_fin}", 
                     font=("Helvetica", 12, "italic")).grid(row=0, column=0, pady=10)

        # Tabs internos del Modal
        self.tabview = ctk.CTkTabview(self, fg_color="#f8f9fa")
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        self.tab_asistencia = self.tabview.add("Asistencia")
        self.tab_comisiones = self.tabview.add("Bases y Comisiones")
        self.tab_ajustes = self.tabview.add("Bonos/Descuentos")

        self._construir_tab_asistencia()
        self._construir_tab_comisiones()
        self._construir_tab_ajustes()
        
        self.grab_set() # Bloquea ventana principal hasta cerrar esta

    # --- Gestión de Horas ---
    def _construir_tab_asistencia(self):
        # Lista de registros del periodo
        self.scroll_asistencia = ctk.CTkScrollableFrame(self.tab_asistencia, fg_color="white")
        self.scroll_asistencia.pack(fill="both", expand=True, padx=10, pady=10)
        self.cargar_asistencia_individual()

    def cargar_asistencia_individual(self):
        for w in self.scroll_asistencia.winfo_children(): w.destroy()
        
        query = """
            SELECT id, entrada, salida, sucursal_id 
            FROM asistencia 
            WHERE empleado_id = %s AND entrada >= %s AND entrada <= %s
            ORDER BY entrada DESC
        """
        registros = ejecutar_query(query, (self.emp_id, self.fecha_inicio, self.fecha_fin), fetch=True)
        
        if registros:
            for r in registros:
                f = ctk.CTkFrame(self.scroll_asistencia, fg_color="#f1f1f1")
                f.pack(fill="x", pady=2)
                
                txt = f"{r['entrada'].strftime('%d/%m %H:%M')} -> "
                txt += r['salida'].strftime('%H:%M') if r['salida'] else "SIN SALIDA"
                
                ctk.CTkLabel(f, text=txt, font=("Helvetica", 12)).pack(side="left", padx=10)
                ctk.CTkButton(f, text="🗑️", width=30, fg_color="#e74c3c", 
                              command=lambda rid=r['id']: self.eliminar_asistencia(rid)).pack(side="right", padx=5)
        else:
            ctk.CTkLabel(self.scroll_asistencia, text="Sin registros en este periodo", text_color="gray").pack(pady=20)

    def eliminar_asistencia(self, rid):
        if messagebox.askyesno("Confirmar", "¿Eliminar este registro de tiempo?"):
            ejecutar_query("DELETE FROM asistencia WHERE id = %s", (rid,))
            self.cargar_asistencia_individual()
            self.callback_refresh()

    # --- Gestión de Bases ---
    def _construir_tab_comisiones(self):
        frame_input = ctk.CTkFrame(self.tab_comisiones, fg_color="transparent")
        frame_input.pack(pady=20)

        # Ahora es un Entry libre en lugar de un OptionMenu
        ctk.CTkLabel(frame_input, text="Capacidad (Cant. Pasteles):").grid(row=0, column=0, padx=5, pady=10)
        self.ent_capacidad = ctk.CTkEntry(frame_input, placeholder_text="Ej: 12", width=120)
        self.ent_capacidad.grid(row=0, column=1, padx=5, pady=10)

        ctk.CTkLabel(frame_input, text="Monto de Comisión ($):").grid(row=1, column=0, padx=5, pady=10)
        self.ent_monto_base = ctk.CTkEntry(frame_input, placeholder_text="Ej: 50.50", width=120)
        self.ent_monto_base.grid(row=1, column=1, padx=5, pady=10)

        ctk.CTkButton(self.tab_comisiones, text="➕ Agregar Comisión", fg_color="#27ae60",
                      command=self.guardar_base).pack(pady=10)

    def guardar_base(self):
        try:
            monto = float(self.ent_monto_base.get())
            cap = int(self.ent_capacidad.get()) # Captura el entero directamente del input
            
            query = """
                INSERT INTO comisiones (empleado_id, tipo_comision, capacidad_base, monto)
                VALUES (%s, 'Base', %s, %s)
            """
            ejecutar_query(query, (self.emp_id, cap, monto))
            
            messagebox.showinfo("Éxito", f"Base de {cap} pasteles registrada por ${monto:.2f}.")
            self.ent_monto_base.delete(0, 'end')
            self.ent_capacidad.delete(0, 'end')
            self.callback_refresh()
        except ValueError:
            messagebox.showerror("Error de Captura", "Verifica que la capacidad sea un número entero y el monto sea numérico.")

    def guardar_base(self):
        try:
            monto = float(self.ent_monto_base.get())
            cap = int(self.cmb_base.get().split()[0])
            query = """
                INSERT INTO comisiones (empleado_id, tipo_comision, capacidad_base, monto)
                VALUES (%s, 'Base', %s, %s)
            """
            ejecutar_query(query, (self.emp_id, cap, monto))
            messagebox.showinfo("Éxito", f"Base de {cap} registrada.")
            self.ent_monto_base.delete(0, 'end')
            self.callback_refresh()
        except:
            messagebox.showerror("Error", "Ingresa un monto válido.")

    def _construir_tab_ajustes(self):
        ctk.CTkLabel(self.tab_ajustes, text="Próximamente: Otros bonos y descuentos.").pack(pady=50)

# =========================================================
# VISTA PRINCIPAL DE NÓMINA
# =========================================================
class NominaFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="white", corner_radius=10)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._construir_filtros()
        self._construir_tabla()
        self.cargar_datos_nomina()

    def _construir_filtros(self):
        frame_top = ctk.CTkFrame(self, fg_color="#f8f9fa", corner_radius=10)
        frame_top.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(frame_top, text="Periodo de Nómina:", font=("Helvetica", 14, "bold"), text_color="#333").pack(side="left", padx=15, pady=15)
        
        hoy = datetime.now()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        
        self.cal_inicio = DateEntry(frame_top, width=12, background='#2c3e50', foreground='white', date_pattern='yyyy-mm-dd')
        self.cal_inicio.set_date(inicio_semana)
        self.cal_inicio.pack(side="left", padx=5)
        
        self.cal_fin = DateEntry(frame_top, width=12, background='#2c3e50', foreground='white', date_pattern='yyyy-mm-dd')
        self.cal_fin.set_date(hoy)
        self.cal_fin.pack(side="left", padx=5)
        
        ctk.CTkButton(frame_top, text="🔄 Calcular Nómina", fg_color="#007bff", 
                      command=self.cargar_datos_nomina).pack(side="left", padx=20)

    def _construir_tabla(self):
        frame_tabla = ctk.CTkFrame(self, fg_color="transparent")
        frame_tabla.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        frame_tabla.grid_rowconfigure(0, weight=1)
        frame_tabla.grid_columnconfigure(0, weight=1)

        columnas = ("id", "nombre", "horas", "sueldo_base", "comisiones", "bonos", "descuentos", "neto")
        self.tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings", selectmode="browse")
        
        # Cabeceras
        for col in columnas: self.tabla.heading(col, text=col.replace("_", " ").title())
        self.tabla.column("id", width=0, stretch=False)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        self.tabla.bind("<Double-1>", self.abrir_editor_empleado)

    def cargar_datos_nomina(self):
        for item in self.tabla.get_children(): self.tabla.delete(item)
        f_ini = self.cal_inicio.get_date().strftime("%Y-%m-%d 00:00:00")
        f_fin = self.cal_fin.get_date().strftime("%Y-%m-%d 23:59:59")

        query = """
            SELECT e.id, e.nombre, e.pago_hora,
                COALESCE(SUM(EXTRACT(EPOCH FROM (a.salida - a.entrada))/3600.0), 0) as horas_totales
            FROM empleados e
            LEFT JOIN asistencia a ON e.id = a.empleado_id 
                AND a.entrada >= %s AND a.salida <= %s
            WHERE e.estatus = 'Activo'
            GROUP BY e.id, e.nombre, e.pago_hora ORDER BY e.nombre
        """
        empleados = ejecutar_query(query, (f_ini, f_fin), fetch=True)
        if not empleados: return

        for emp in empleados:
            # Cálculos adicionales
            q_com = "SELECT COALESCE(SUM(monto), 0) as t FROM comisiones WHERE empleado_id=%s AND fecha>=%s AND fecha<=%s"
            com = float(ejecutar_query(q_com, (emp['id'], f_ini, f_fin), fetch=True)[0]['t'])
            
            # Lógica financiera V2
            calc = NominaController.calcular_pago_neto(float(emp['horas_totales']), float(emp['pago_hora']), com, 0, 0)

            self.tabla.insert("", "end", values=(
                emp['id'], emp['nombre'], f"{calc['horas_calculadas']:.2f}h",
                f"${calc['sueldo_tiempo']:.2f}", f"${calc['comisiones_base']:.2f}",
                "$0.00", "$0.00", f"${calc['pago_neto']:.2f}"
            ))

    def abrir_editor_empleado(self, event):
        sel = self.tabla.selection()
        if not sel: return
        vals = self.tabla.item(sel)['values']
        
        # Lanzar el nuevo Modal
        EditorAuditoriaModal(
            self, 
            emp_id=vals[0], 
            nombre=vals[1], 
            fecha_inicio=self.cal_inicio.get_date().strftime("%Y-%m-%d"),
            fecha_fin=self.cal_fin.get_date().strftime("%Y-%m-%d"),
            callback_refresh=self.cargar_datos_nomina
        )