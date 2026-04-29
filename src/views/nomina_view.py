import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry
from src.models.db_manager import ejecutar_query
from src.controllers.nomina_controller import NominaController

import pandas as pd
from tkinter import filedialog
import os

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
        
        f_ini = f"{self.fecha_inicio} 00:00:00"
        f_fin = f"{self.fecha_fin} 23:59:59"
        
        query = """
            SELECT id, entrada, salida, sucursal_id 
            FROM asistencia 
            WHERE empleado_id = %s AND entrada >= %s AND entrada <= %s
            ORDER BY entrada DESC
        """
        registros = ejecutar_query(query, (self.emp_id, f_ini, f_fin), fetch=True)
        
        if registros:
            for r in registros:
                f = ctk.CTkFrame(self.scroll_asistencia, fg_color="#f1f1f1")
                f.pack(fill="x", pady=2)
                
                # Formateo visual del texto
                txt = f"{r['entrada'].strftime('%d/%m %H:%M')} -> "
                txt += r['salida'].strftime('%H:%M') if r['salida'] else "SIN SALIDA"
                
                ctk.CTkLabel(f, text=txt, font=("Helvetica", 12)).pack(side="left", padx=10)
                
                # Contenedor de botones de acción
                f_botones = ctk.CTkFrame(f, fg_color="transparent")
                f_botones.pack(side="right", padx=5)
                
                # Botón de Borrar (Existente)
                ctk.CTkButton(f_botones, text="🗑️", width=30, fg_color="#e74c3c", hover_color="#c0392b",
                              command=lambda rid=r['id']: self.eliminar_asistencia(rid)).pack(side="right", padx=2)
                
                # NUEVO: Botón de Editar
                ctk.CTkButton(f_botones, text="✏️", width=30, fg_color="#f39c12", hover_color="#d68910",
                              command=lambda rid=r['id'], ent=r['entrada'], sal=r['salida']: self.abrir_editor_tiempo(rid, ent, sal)).pack(side="right", padx=2)
        else:
            ctk.CTkLabel(self.scroll_asistencia, text="Sin registros en este periodo", text_color="gray").pack(pady=20)

    # --- NUEVAS FUNCIONES DE EDICIÓN ---
    def abrir_editor_tiempo(self, rid, entrada_actual, salida_actual):
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
        ent_entrada.insert(0, entrada_actual.strftime('%Y-%m-%d %H:%M') if entrada_actual else "")

        ctk.CTkLabel(modal, text="Hora de Salida (YYYY-MM-DD HH:MM):", font=("Helvetica", 12, "bold")).pack(pady=(15, 0))
        ent_salida = ctk.CTkEntry(modal, width=220, justify="center")
        ent_salida.pack(pady=5)
        # Pre-llenamos con el valor actual, si no tiene salida, lo dejamos en blanco
        ent_salida.insert(0, salida_actual.strftime('%Y-%m-%d %H:%M') if salida_actual else "")
        
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
    # --- FIN DE NUEVAS FUNCIONES ---

    def eliminar_asistencia(self, rid):
        if messagebox.askyesno("Confirmar", "¿Eliminar este registro de tiempo?"):
            ejecutar_query("DELETE FROM asistencia WHERE id = %s", (rid,))
            self.cargar_asistencia_individual()
            self.callback_refresh()

    # --- Gestión de Bases ---
    def _construir_tab_comisiones(self):
        # 1. Zona de Captura (Arriba)
        frame_input = ctk.CTkFrame(self.tab_comisiones, fg_color="transparent")
        frame_input.pack(pady=10)

        ctk.CTkLabel(frame_input, text="Capacidad (Pasteles):").grid(row=0, column=0, padx=5, pady=5)
        self.ent_capacidad = ctk.CTkEntry(frame_input, placeholder_text="Ej: 12", width=120)
        self.ent_capacidad.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_input, text="Monto ($):").grid(row=1, column=0, padx=5, pady=5)
        self.ent_monto_base = ctk.CTkEntry(frame_input, placeholder_text="Ej: 500", width=120)
        self.ent_monto_base.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkButton(self.tab_comisiones, text="➕ Agregar Comisión", fg_color="#27ae60",
                      command=self.guardar_base).pack(pady=10)

        # 2. Zona de Historial (Abajo)
        ctk.CTkLabel(self.tab_comisiones, text="Historial del Periodo Auditado", font=("Helvetica", 12, "bold")).pack(pady=(15, 5))
        
        self.scroll_comisiones = ctk.CTkScrollableFrame(self.tab_comisiones, fg_color="white")
        self.scroll_comisiones.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.cargar_historial_comisiones()

    def cargar_historial_comisiones(self):
        for w in self.scroll_comisiones.winfo_children(): w.destroy()
        
        query = """
            SELECT id, fecha, capacidad_base, monto 
            FROM comisiones 
            WHERE empleado_id = %s AND fecha >= %s AND fecha <= %s
            ORDER BY fecha DESC
        """
        registros = ejecutar_query(query, (self.emp_id, self.fecha_inicio, self.fecha_fin), fetch=True)
        
        if registros:
            for r in registros:
                f = ctk.CTkFrame(self.scroll_comisiones, fg_color="#f1f1f1")
                f.pack(fill="x", pady=2)
                
                txt = f"{r['fecha'].strftime('%d/%m/%Y')} - Base de {r['capacidad_base']}: ${r['monto']}"
                ctk.CTkLabel(f, text=txt, font=("Helvetica", 12)).pack(side="left", padx=10)
                
                ctk.CTkButton(f, text="🗑️", width=30, fg_color="#e74c3c", 
                              command=lambda rid=r['id']: self.eliminar_comision(rid)).pack(side="right", padx=5)
        else:
            ctk.CTkLabel(self.scroll_comisiones, text="Sin comisiones registradas en este periodo", text_color="gray").pack(pady=20)

    def eliminar_comision(self, rid):
        if messagebox.askyesno("Confirmar", "¿Eliminar permanentemente esta comisión?"):
            ejecutar_query("DELETE FROM comisiones WHERE id = %s", (rid,))
            self.cargar_historial_comisiones() # Refresca la lista interna
            self.callback_refresh()            # Refresca la tabla maestra

    def guardar_base(self):
        try:
            monto = float(self.ent_monto_base.get())
            cap = int(self.ent_capacidad.get())
            
            # Inyectamos self.fecha_fin explícitamente para que la comisión caiga dentro del periodo auditado
            query = """
                INSERT INTO comisiones (empleado_id, tipo_comision, capacidad_base, monto, fecha)
                VALUES (%s, 'Base', %s, %s, %s)
            """
            exito = ejecutar_query(query, (self.emp_id, cap, monto, self.fecha_fin))
            
            if exito is True:
                self.ent_monto_base.delete(0, 'end')
                self.ent_capacidad.delete(0, 'end')
                self.cargar_historial_comisiones() # Refresca la lista interna
                self.callback_refresh()            # Refresca la tabla maestra
            else:
                messagebox.showerror("Error SQL", f"La base de datos rechazó la operación:\n{exito}")
                
        except ValueError:
            messagebox.showerror("Error de Captura", "Verifica que la capacidad sea un número entero (ej: 5) y el monto sea numérico (ej: 500).")

    # --- Gestión de Bonos y Descuentos ---
    # --- REEMPLAZAR DESDE AQUÍ HASTA EL FINAL DE LA CLASE EditorAuditoriaModal ---
    def _construir_tab_ajustes(self):
        frame_input = ctk.CTkFrame(self.tab_ajustes, fg_color="transparent")
        frame_input.pack(pady=10)

        ctk.CTkLabel(frame_input, text="Tipo:").grid(row=0, column=0, padx=5)
        self.cmb_tipo_ajuste = ctk.CTkOptionMenu(frame_input, values=["Bono", "Descuento"], width=120)
        self.cmb_tipo_ajuste.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(frame_input, text="Monto ($):").grid(row=0, column=2, padx=5)
        self.ent_monto_ajuste = ctk.CTkEntry(frame_input, placeholder_text="Monto", width=100)
        self.ent_monto_ajuste.grid(row=0, column=3, padx=5)

        ctk.CTkLabel(frame_input, text="Motivo:").grid(row=1, column=0, padx=5, pady=10)
        self.ent_motivo_ajuste = ctk.CTkEntry(frame_input, placeholder_text="Ej: Bono puntualidad / Retardo", width=250)
        self.ent_motivo_ajuste.grid(row=1, column=1, columnspan=3, padx=5, pady=10, sticky="ew")

        ctk.CTkButton(self.tab_ajustes, text="💾 Aplicar Ajuste", fg_color="#2980b9",
                      command=self.guardar_ajuste).pack(pady=10)

        self.scroll_ajustes = ctk.CTkScrollableFrame(self.tab_ajustes, fg_color="white")
        self.scroll_ajustes.pack(fill="both", expand=True, padx=10, pady=5)
        self.cargar_historial_ajustes()

    def cargar_historial_ajustes(self):
        for w in self.scroll_ajustes.winfo_children(): w.destroy()
        
        # Expandimos límites para que detecte ajustes de hoy
        f_ini = f"{self.fecha_inicio} 00:00:00"
        f_fin = f"{self.fecha_fin} 23:59:59"
        
        query = "SELECT id, fecha, monto, tipo, motivo FROM ajustes WHERE empleado_id = %s AND fecha >= %s AND fecha <= %s"
        registros = ejecutar_query(query, (self.emp_id, f_ini, f_fin), fetch=True)
        
        if registros:
            for r in registros:
                color = "#27ae60" if r['tipo'] == 'Bono' else "#e74c3c"
                f = ctk.CTkFrame(self.scroll_ajustes, fg_color="#f1f1f1")
                f.pack(fill="x", pady=2)
                txt = f"[{r['tipo']}] ${r['monto']} - {r['motivo']}"
                ctk.CTkLabel(f, text=txt, font=("Helvetica", 11), text_color=color).pack(side="left", padx=10)
                ctk.CTkButton(f, text="🗑️", width=30, fg_color="#e74c3c", command=lambda rid=r['id']: self.eliminar_ajuste(rid)).pack(side="right", padx=5)

    def guardar_ajuste(self):
        try:
            monto = float(self.ent_monto_ajuste.get())
            tipo = self.cmb_tipo_ajuste.get()
            motivo = self.ent_motivo_ajuste.get()
            
            query = "INSERT INTO ajustes (empleado_id, monto, tipo, motivo, fecha) VALUES (%s, %s, %s, %s, %s)"
            # Guardamos con la fecha_fin para que entre en el periodo actual
            ejecutar_query(query, (self.emp_id, monto, tipo, motivo, self.fecha_fin))
            
            self.cargar_historial_ajustes()
            self.callback_refresh()
            self.ent_monto_ajuste.delete(0, 'end')
            self.ent_motivo_ajuste.delete(0, 'end')
        except ValueError: 
            messagebox.showerror("Error", "El monto debe ser numérico")

    def eliminar_ajuste(self, rid):
        ejecutar_query("DELETE FROM ajustes WHERE id = %s", (rid,))
        self.cargar_historial_ajustes()
        self.callback_refresh()
    # --- FIN DEL REEMPLAZO ---
        ejecutar_query("DELETE FROM ajustes WHERE id = %s", (rid,))
        self.cargar_historial_ajustes()
        self.callback_refresh()

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
        
        ctk.CTkButton(frame_top, text="📥 Exportar a Excel", fg_color="#28a745", hover_color="#218838", command=self.exportar_excel).pack(side="left", padx=5)

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
            # --- REEMPLAZAR EL INTERIOR DEL BUCLE POR ESTO ---
            emp_id = emp['id']
            horas = float(emp['horas_totales'])
            pago_hora = float(emp['pago_hora'])
            
            # Sub-queries
            q_com = "SELECT COALESCE(SUM(monto), 0) as t FROM comisiones WHERE empleado_id=%s AND fecha>=%s AND fecha<=%s"
            comisiones = float(ejecutar_query(q_com, (emp_id, f_ini, f_fin), fetch=True)[0]['t'])
            
            q_bonos = "SELECT COALESCE(SUM(monto), 0) as t FROM ajustes WHERE empleado_id=%s AND tipo='Bono' AND fecha>=%s AND fecha<=%s"
            bonos = float(ejecutar_query(q_bonos, (emp_id, f_ini, f_fin), fetch=True)[0]['t'])
            
            q_desc = "SELECT COALESCE(SUM(monto), 0) as t FROM ajustes WHERE empleado_id=%s AND tipo='Descuento' AND fecha>=%s AND fecha<=%s"
            descuentos = float(ejecutar_query(q_desc, (emp_id, f_ini, f_fin), fetch=True)[0]['t'])

            # Lógica financiera (Ya le pasamos los bonos y descuentos)
            calc = NominaController.calcular_pago_neto(horas, pago_hora, comisiones, bonos, descuentos)

            self.tabla.insert("", "end", values=(
                emp_id, 
                emp['nombre'], 
                f"{calc['horas_calculadas']:.2f}h",
                f"${calc['sueldo_tiempo']:.2f}", 
                f"${calc['comisiones_base']:.2f}",
                f"${calc['bonos']:.2f}", 
                f"${calc['descuentos']:.2f}", 
                f"${calc['pago_neto']:.2f}"
            ))
            # --- FIN DEL REEMPLAZO ---

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

    def exportar_excel(self):
        # 1. Extraer los datos directamente de la tabla visual
        filas = []
        for item in self.tabla.get_children():
            valores = self.tabla.item(item)['values']
            filas.append(valores)
            
        if not filas:
            messagebox.showwarning("Aviso", "No hay datos en la tabla para exportar. Calcula la nómina primero.")
            return

        # 2. Definir las columnas excluyendo el ID interno
        columnas = ["ID", "Empleado", "Horas Trabajadas", "Sueldo Tiempo", "Comisiones Base", "Otros Bonos", "Descuentos", "Neto a Pagar"]
        
        df = pd.DataFrame(filas, columns=columnas)
        
        # Opcional: Limpiar el ID interno del Excel para que sea un reporte puramente financiero
        df = df.drop(columns=["ID"])

        # 3. Diálogo para guardar el archivo
        fecha_ini = self.cal_inicio.get_date().strftime("%Y%m%d")
        fecha_fin = self.cal_fin.get_date().strftime("%Y%m%d")
        nombre_default = f"Nomina_Jesusito_{fecha_ini}_al_{fecha_fin}.xlsx"

        ruta_archivo = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=nombre_default,
            title="Guardar Reporte de Nómina",
            filetypes=[("Archivos de Excel", "*.xlsx")]
        )

        if ruta_archivo:
            try:
                # 4. Generar el archivo
                df.to_excel(ruta_archivo, index=False, engine='openpyxl')
                messagebox.showinfo("Éxito", f"Reporte guardado exitosamente en:\n{ruta_archivo}")
                
                # Auto-abrir el archivo en Windows
                os.startfile(ruta_archivo)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{e}")