import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry
from src.models.db_manager import ejecutar_query
from src.controllers.nomina_controller import NominaController

import pandas as pd
from tkinter import filedialog
import os

# ... (Clase EditorAuditoriaModal se mantiene igual, ya está optimizada para registros individuales) ...
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

        self.tabview = ctk.CTkTabview(self, fg_color="#f8f9fa")
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        self.tab_asistencia = self.tabview.add("Asistencia")
        self.tab_comisiones = self.tabview.add("Bases y Comisiones")
        self.tab_ajustes = self.tabview.add("Bonos/Descuentos")

        self._construir_tab_asistencia()
        self._construir_tab_comisiones()
        self._construir_tab_ajustes()
        self.grab_set()

    def _construir_tab_asistencia(self):
        self.scroll_asistencia = ctk.CTkScrollableFrame(self.tab_asistencia, fg_color="white")
        self.scroll_asistencia.pack(fill="both", expand=True, padx=10, pady=10)
        self.cargar_asistencia_individual()

    def cargar_asistencia_individual(self):
        for w in self.scroll_asistencia.winfo_children(): w.destroy()
        f_ini = f"{self.fecha_inicio} 00:00:00"
        f_fin = f"{self.fecha_fin} 23:59:59"
        query = "SELECT id, entrada, salida FROM asistencia WHERE empleado_id = %s AND entrada >= %s AND entrada <= %s ORDER BY entrada DESC"
        registros = ejecutar_query(query, (self.emp_id, f_ini, f_fin), fetch=True)
        if registros:
            for r in registros:
                f = ctk.CTkFrame(self.scroll_asistencia, fg_color="#f1f1f1")
                f.pack(fill="x", pady=2)
                txt = f"{r['entrada'].strftime('%d/%m %H:%M')} -> {r['salida'].strftime('%H:%M') if r['salida'] else 'SIN SALIDA'}"
                ctk.CTkLabel(f, text=txt, font=("Helvetica", 12)).pack(side="left", padx=10)
                f_botones = ctk.CTkFrame(f, fg_color="transparent")
                f_botones.pack(side="right", padx=5)
                ctk.CTkButton(f_botones, text="🗑️", width=30, fg_color="#e74c3c", command=lambda rid=r['id']: self.eliminar_asistencia(rid)).pack(side="right", padx=2)
                ctk.CTkButton(f_botones, text="✏️", width=30, fg_color="#f39c12", command=lambda rid=r['id'], ent=r['entrada'], sal=r['salida']: self.abrir_editor_tiempo(rid, ent, sal)).pack(side="right", padx=2)

    def abrir_editor_tiempo(self, rid, ent, sal):
        modal = ctk.CTkToplevel(self)
        modal.title("Auditoría de Tiempo")
        modal.geometry("350x280")
        modal.grab_set() # Bloquea la ventana inferior

        # Centrar ventana
        modal.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 175
        y = self.winfo_y() + (self.winfo_height() // 2) - 140
        modal.geometry(f"+{x}+{y}")

        ctk.CTkLabel(modal, text="Hora de Entrada (YYYY-MM-DD HH:MM):", font=("Helvetica", 12, "bold")).pack(pady=(15, 0))
        ent_entrada = ctk.CTkEntry(modal, width=220, justify="center")
        ent_entrada.pack(pady=5)
        # Pre-llenamos con el valor actual
        ent_entrada.insert(0, ent.strftime('%Y-%m-%d %H:%M') if ent else "")

        ctk.CTkLabel(modal, text="Hora de Salida (YYYY-MM-DD HH:MM):", font=("Helvetica", 12, "bold")).pack(pady=(15, 0))
        ent_salida = ctk.CTkEntry(modal, width=220, justify="center")
        ent_salida.pack(pady=5)
        # Pre-llenamos con el valor actual, si no tiene salida, lo dejamos en blanco
        ent_salida.insert(0, sal.strftime('%Y-%m-%d %H:%M') if sal else "")
        
        ctk.CTkLabel(modal, text="* Deja la salida en blanco si el turno sigue abierto", font=("Helvetica", 10, "italic"), text_color="gray").pack()

        ctk.CTkButton(modal, text="💾 Aplicar Corrección", fg_color="#28a745", hover_color="#218838",
                      command=lambda: self.guardar_edicion_tiempo(rid, ent_entrada.get(), ent_salida.get(), modal)).pack(pady=20)

    def guardar_edicion_tiempo(self, rid, str_entrada, str_salida, ventana):
        try:
            # 1. Validación de parseo estricto para evitar corromper la BD
            if str_entrada: 
                datetime.strptime(str_entrada, '%Y-%m-%d %H:%M')
            else:
                return messagebox.showwarning("Auditoría", "La hora de entrada no puede estar vacía.")
                
            val_salida = None
            if str_salida.strip():
                datetime.strptime(str_salida, '%Y-%m-%d %H:%M')
                val_salida = str_salida.strip()

            # 2. Ejecutar Update
            query = "UPDATE asistencia SET entrada = %s, salida = %s WHERE id = %s"
            exito = ejecutar_query(query, (str_entrada, val_salida, rid))

            if exito is True:
                ventana.destroy()
                self.cargar_asistencia_individual() # Refresca el sub-modal
                self.callback_refresh()             # Refresca la tabla matriz
            else:
                messagebox.showerror("Error SQL", f"La nube rechazó la operación:\n{exito}")
                
        except ValueError:
            messagebox.showerror("Fallo de Sintaxis", "Utiliza exactamente el formato militar de 24 hrs:\n\nYYYY-MM-DD HH:MM\nEjemplo: 2026-04-29 14:30")

    def eliminar_asistencia(self, rid):
        if messagebox.askyesno("Confirmar", "¿Eliminar registro?"):
            ejecutar_query("DELETE FROM asistencia WHERE id = %s", (rid,))
            self.cargar_asistencia_individual()
            self.callback_refresh()

    def _construir_tab_comisiones(self):
        frame_input = ctk.CTkFrame(self.tab_comisiones, fg_color="transparent")
        frame_input.pack(pady=10)
        self.ent_capacidad = ctk.CTkEntry(frame_input, placeholder_text="Capacidad", width=120)
        self.ent_capacidad.grid(row=0, column=0, padx=5)
        self.ent_monto_base = ctk.CTkEntry(frame_input, placeholder_text="Monto $", width=120)
        self.ent_monto_base.grid(row=0, column=1, padx=5)
        ctk.CTkButton(self.tab_comisiones, text="➕ Agregar", command=self.guardar_base).pack(pady=10)
        self.scroll_comisiones = ctk.CTkScrollableFrame(self.tab_comisiones, fg_color="white")
        self.scroll_comisiones.pack(fill="both", expand=True, padx=10)
        self.cargar_historial_comisiones()

    def cargar_historial_comisiones(self):
        for w in self.scroll_comisiones.winfo_children(): w.destroy()
        query = "SELECT id, fecha, capacidad_base, monto FROM comisiones WHERE empleado_id = %s AND fecha >= %s AND fecha <= %s ORDER BY fecha DESC"
        registros = ejecutar_query(query, (self.emp_id, self.fecha_inicio, self.fecha_fin), fetch=True)
        if registros:
            for r in registros:
                f = ctk.CTkFrame(self.scroll_comisiones, fg_color="#f1f1f1")
                f.pack(fill="x", pady=2)
                ctk.CTkLabel(f, text=f"{r['fecha'].strftime('%d/%m')} - Base {r['capacidad_base']}: ${r['monto']}").pack(side="left", padx=10)
                ctk.CTkButton(f, text="🗑️", width=30, fg_color="#e74c3c", command=lambda rid=r['id']: self.eliminar_comision(rid)).pack(side="right", padx=5)

    def eliminar_comision(self, rid):
        ejecutar_query("DELETE FROM comisiones WHERE id = %s", (rid,))
        self.cargar_historial_comisiones()
        self.callback_refresh()

    def guardar_base(self):
        try:
            m = float(self.ent_monto_base.get()); c = int(self.ent_capacidad.get())
            ejecutar_query("INSERT INTO comisiones (empleado_id, tipo_comision, capacidad_base, monto, fecha) VALUES (%s, 'Base', %s, %s, %s)", (self.emp_id, c, m, self.fecha_fin))
            self.cargar_historial_comisiones(); self.callback_refresh()
        except: pass

    def _construir_tab_ajustes(self):
        frame_input = ctk.CTkFrame(self.tab_ajustes, fg_color="transparent"); frame_input.pack(pady=10)
        self.cmb_tipo_ajuste = ctk.CTkOptionMenu(frame_input, values=["Bono", "Descuento"], width=120); self.cmb_tipo_ajuste.grid(row=0, column=0, padx=5)
        self.ent_monto_ajuste = ctk.CTkEntry(frame_input, width=100); self.ent_monto_ajuste.grid(row=0, column=1, padx=5)
        self.ent_motivo_ajuste = ctk.CTkEntry(frame_input, width=200); self.ent_motivo_ajuste.grid(row=1, column=0, columnspan=2, pady=10)
        ctk.CTkButton(self.tab_ajustes, text="💾 Aplicar", command=self.guardar_ajuste).pack()
        self.scroll_ajustes = ctk.CTkScrollableFrame(self.tab_ajustes, fg_color="white"); self.scroll_ajustes.pack(fill="both", expand=True)
        self.cargar_historial_ajustes()

    def cargar_historial_ajustes(self):
        for w in self.scroll_ajustes.winfo_children(): w.destroy()
        query = "SELECT id, monto, tipo, motivo FROM ajustes WHERE empleado_id = %s AND fecha >= %s AND fecha <= %s"
        registros = ejecutar_query(query, (self.emp_id, self.fecha_inicio, self.fecha_fin), fetch=True)
        if registros:
            for r in registros:
                f = ctk.CTkFrame(self.scroll_ajustes, fg_color="#f1f1f1"); f.pack(fill="x", pady=2)
                ctk.CTkLabel(f, text=f"[{r['tipo']}] ${r['monto']} - {r['motivo']}").pack(side="left", padx=10)
                ctk.CTkButton(f, text="🗑️", width=30, fg_color="#e74c3c", command=lambda rid=r['id']: self.eliminar_ajuste(rid)).pack(side="right", padx=5)

    def guardar_ajuste(self):
        try:
            m = float(self.ent_monto_ajuste.get()); t = self.cmb_tipo_ajuste.get(); mot = self.ent_motivo_ajuste.get()
            ejecutar_query("INSERT INTO ajustes (empleado_id, monto, tipo, motivo, fecha) VALUES (%s, %s, %s, %s, %s)", (self.emp_id, m, t, mot, self.fecha_fin))
            self.cargar_historial_ajustes(); self.callback_refresh()
        except: pass

    def eliminar_ajuste(self, rid):
        ejecutar_query("DELETE FROM ajustes WHERE id = %s", (rid,))
        self.cargar_historial_ajustes(); self.callback_refresh()

# =========================================================
# VISTA PRINCIPAL DE NÓMINA (OPTIMIZADA)
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
        
        ctk.CTkLabel(frame_top, text="Periodo:", font=("Helvetica", 14, "bold")).pack(side="left", padx=15)
        
        hoy = datetime.now()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        
        self.cal_inicio = DateEntry(frame_top, width=12, background='#2c3e50', foreground='white', date_pattern='yyyy-mm-dd')
        self.cal_inicio.set_date(inicio_semana)
        self.cal_inicio.pack(side="left", padx=5)
        
        self.cal_fin = DateEntry(frame_top, width=12, background='#2c3e50', foreground='white', date_pattern='yyyy-mm-dd')
        self.cal_fin.set_date(hoy)
        self.cal_fin.pack(side="left", padx=5)
        
        ctk.CTkButton(frame_top, text="🔄 Recalcular", fg_color="#007bff", command=self.cargar_datos_nomina).pack(side="left", padx=20)
        ctk.CTkButton(frame_top, text="📥 Excel", fg_color="#28a745", command=self.exportar_excel).pack(side="left")

    def _construir_tabla(self):
        frame_tabla = ctk.CTkFrame(self, fg_color="transparent")
        frame_tabla.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        frame_tabla.grid_rowconfigure(0, weight=1)
        frame_tabla.grid_columnconfigure(0, weight=1)

        columnas = ("id", "nombre", "horas", "sueldo_base", "comisiones", "bonos", "descuentos", "neto")
        self.tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
        for col in columnas: self.tabla.heading(col, text=col.replace("_", " ").title())
        self.tabla.column("id", width=0, stretch=False)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        self.tabla.bind("<Double-1>", self.abrir_editor_empleado)

    # --- MÉTODO CRÍTICO OPTIMIZADO: DE 15s A <1s ---
    def cargar_datos_nomina(self):
        for item in self.tabla.get_children(): self.tabla.delete(item)
        
        f_ini = self.cal_inicio.get_date().strftime("%Y-%m-%d 00:00:00")
        f_fin = self.cal_fin.get_date().strftime("%Y-%m-%d 23:59:59")

        # CONSULTA MAESTRA (BATCH): Sumamos todo en la nube de un solo viaje
        query_maestra = """
            SELECT 
                e.id, 
                e.nombre, 
                e.pago_hora,
                -- 1. Cálculo de horas
                (SELECT COALESCE(SUM(EXTRACT(EPOCH FROM (salida - entrada))/3600.0), 0) 
                 FROM asistencia WHERE empleado_id = e.id AND entrada >= %s AND salida <= %s) as horas_totales,
                -- 2. Suma de comisiones
                (SELECT COALESCE(SUM(monto), 0) 
                 FROM comisiones WHERE empleado_id = e.id AND fecha >= %s AND fecha <= %s) as total_comisiones,
                -- 3. Suma de bonos
                (SELECT COALESCE(SUM(monto), 0) 
                 FROM ajustes WHERE empleado_id = e.id AND tipo = 'Bono' AND fecha >= %s AND fecha <= %s) as total_bonos,
                -- 4. Suma de descuentos
                (SELECT COALESCE(SUM(monto), 0) 
                 FROM ajustes WHERE empleado_id = e.id AND tipo = 'Descuento' AND fecha >= %s AND fecha <= %s) as total_descuentos
            FROM empleados e
            WHERE e.estatus = 'Activo'
            ORDER BY e.nombre
        """
        
        # Parámetros para cada subconsulta (repetimos el rango de fechas)
        params = (f_ini, f_fin, f_ini, f_fin, f_ini, f_fin, f_ini, f_fin)
        
        # ÚNICA PETICIÓN A LA NUBE
        datos = ejecutar_query(query_maestra, params, fetch=True)

        if datos:
            for d in datos:
                # Los cálculos financieros ahora son locales (instantáneos)
                calc = NominaController.calcular_pago_neto(
                    float(d['horas_totales']), 
                    float(d['pago_hora']), 
                    float(d['total_comisiones']), 
                    float(d['total_bonos']), 
                    float(d['total_descuentos'])
                )

                self.tabla.insert("", "end", values=(
                    d['id'], 
                    d['nombre'], 
                    f"{calc['horas_calculadas']:.2f}h",
                    f"${calc['sueldo_tiempo']:.2f}", 
                    f"${calc['comisiones_base']:.2f}",
                    f"${calc['bonos']:.2f}", 
                    f"${calc['descuentos']:.2f}", 
                    f"${calc['pago_neto']:.2f}"
                ))

    def abrir_editor_empleado(self, event):
        sel = self.tabla.selection()
        if not sel: return
        vals = self.tabla.item(sel)['values']
        EditorAuditoriaModal(self, vals[0], vals[1], self.cal_inicio.get_date().strftime("%Y-%m-%d"), self.cal_fin.get_date().strftime("%Y-%m-%d"), self.cargar_datos_nomina)

    def exportar_excel(self):
        filas = [self.tabla.item(i)['values'] for i in self.tabla.get_children()]
        if not filas: return
        df = pd.DataFrame(filas, columns=["ID", "Empleado", "Horas", "Sueldo", "Comisiones", "Bonos", "Descuentos", "Neto"]).drop(columns=["ID"])
        ruta = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="Nomina_Jesusito.xlsx")
        if ruta: df.to_excel(ruta, index=False); os.startfile(ruta)