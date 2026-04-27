import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import sqlite3

class GerencialFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="white", corner_radius=10)
        
        self.lbl_titulo = ctk.CTkLabel(self, text="MANTENIMIENTO Y AUDITORÍA", font=("Helvetica", 18, "bold"), text_color="#1a1a1a")
        self.lbl_titulo.pack(pady=15)

        # --- SISTEMA DE PESTAÑAS ---
        self.tabview = ctk.CTkTabview(self, width=800, height=500, fg_color="#f8f9fa", segmented_button_fg_color="#e9ecef", segmented_button_selected_color="#007bff")
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tab_bonos = self.tabview.add("Bonos y Descuentos")
        self.tab_auditoria = self.tabview.add("Auditoría de Asistencia")
        self.tab_sistema = self.tabview.add("Sistema y Seguridad")

        self._construir_tab_bonos()
        self._construir_tab_auditoria()
        self._construir_tab_sistema()

    # ==========================================
    # PESTAÑA 1: BONOS Y DESCUENTOS
    # ==========================================
    def _construir_tab_bonos(self):
        frame_form = ctk.CTkFrame(self.tab_bonos, fg_color="transparent")
        frame_form.pack(pady=20, padx=40, fill="x")

        ctk.CTkLabel(frame_form, text="Empleado:", font=("Helvetica", 12, "bold"), text_color="#333").pack(pady=(10, 0))
        self.cmb_empleados_bono = ctk.CTkOptionMenu(frame_form, values=self.obtener_lista_empleados(), width=250)
        self.cmb_empleados_bono.pack(pady=5)

        self.tipo_ajuste = ctk.CTkSegmentedButton(frame_form, values=["Bono", "Descuento"], width=250)
        self.tipo_ajuste.set("Bono")
        self.tipo_ajuste.pack(pady=15)

        frame_inputs = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_inputs.pack(pady=10)

        self.ent_monto = ctk.CTkEntry(frame_inputs, placeholder_text="Monto $ (ej: 500)", width=120)
        self.ent_monto.pack(side="left", padx=5)

        self.ent_motivo = ctk.CTkEntry(frame_inputs, placeholder_text="Motivo (ej: Puntualidad)", width=200)
        self.ent_motivo.pack(side="left", padx=5)

        ctk.CTkButton(frame_form, text="Registrar en Nómina", fg_color="#28a745", hover_color="#218838",
                      width=250, font=("Helvetica", 12, "bold"), command=self.guardar_ajuste_db).pack(pady=20)

    def guardar_ajuste_db(self):
        empleado = self.cmb_empleados_bono.get()
        monto = self.ent_monto.get()
        tipo = self.tipo_ajuste.get()
        motivo = self.ent_motivo.get()
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")

        if not monto or not motivo or empleado in ["No hay empleados", "Error de conexión"]:
            messagebox.showwarning("Faltan Datos", "Por favor ingresa el monto y el motivo.")
            return

        try:
            monto_val = float(monto)
            from src.models.db_manager import crear_conexion
            conn = crear_conexion()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ajustes (empleado_nombre, fecha, monto, tipo, motivo)
                VALUES (?, ?, ?, ?, ?)
            """, (empleado, fecha_hoy, monto_val, tipo, motivo))
            conn.commit()
            conn.close()
            messagebox.showinfo("Registrado", f"Se aplicó un {tipo} de ${monto_val} a {empleado}")
            self.ent_monto.delete(0, 'end')
            self.ent_motivo.delete(0, 'end')
        except ValueError:
            messagebox.showerror("Error", "El monto debe ser un número (ej: 150.50)")
        except Exception as e:
            messagebox.showerror("Error", f"Error de BD: {e}")

    # ==========================================
    # PESTAÑA 2: AUDITORÍA DE ASISTENCIA (NUEVO CRUD)
    # ==========================================
    def _construir_tab_auditoria(self):
        # Buscador superior
        frame_busqueda = ctk.CTkFrame(self.tab_auditoria, fg_color="transparent")
        frame_busqueda.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_busqueda, text="Empleado:").pack(side="left", padx=5)
        self.cmb_empleado_auditoria = ctk.CTkOptionMenu(frame_busqueda, values=self.obtener_lista_empleados(), width=200)
        self.cmb_empleado_auditoria.pack(side="left", padx=5)

        ctk.CTkLabel(frame_busqueda, text="Fecha (YYYY-MM-DD):").pack(side="left", padx=(15, 5))
        self.ent_fecha_auditoria = ctk.CTkEntry(frame_busqueda, width=120)
        self.ent_fecha_auditoria.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_fecha_auditoria.pack(side="left", padx=5)

        ctk.CTkButton(frame_busqueda, text="🔍 Buscar Registros", width=120, command=self.buscar_registros_asistencia).pack(side="left", padx=15)

        # Contenedor de resultados
        self.scroll_auditoria = ctk.CTkScrollableFrame(self.tab_auditoria, fg_color="white", corner_radius=5)
        self.scroll_auditoria.pack(fill="both", expand=True, padx=20, pady=10)

        # Controles para AGREGAR un registro manual
        frame_agregar = ctk.CTkFrame(self.tab_auditoria, fg_color="#e9ecef", corner_radius=5)
        frame_agregar.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_agregar, text="Agregar Registro Manual:", font=("Helvetica", 12, "bold")).pack(side="left", padx=10)
        
        self.ent_nueva_hora = ctk.CTkEntry(frame_agregar, placeholder_text="Hora (ej: 08:00:00)", width=130)
        self.ent_nueva_hora.pack(side="left", padx=5)
        
        self.cmb_nuevo_tipo = ctk.CTkOptionMenu(frame_agregar, values=["Entrada", "Salida"], width=100)
        self.cmb_nuevo_tipo.pack(side="left", padx=5)
        
        ctk.CTkButton(frame_agregar, text="➕ Insertar", fg_color="#007bff", width=100, command=self.insertar_registro_manual).pack(side="left", padx=15)

    def buscar_registros_asistencia(self):
        empleado = self.cmb_empleado_auditoria.get()
        fecha = self.ent_fecha_auditoria.get()

        for widget in self.scroll_auditoria.winfo_children():
            widget.destroy()

        from src.models.db_manager import crear_conexion
        conn = crear_conexion()
        if not conn: return
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, hora, tipo_registro FROM asistencia WHERE empleado_nombre=? AND fecha=? ORDER BY hora", (empleado, fecha))
        filas = cursor.fetchall()
        conn.close()

        if not filas:
            ctk.CTkLabel(self.scroll_auditoria, text="No hay registros para esta fecha.", text_color="#666").pack(pady=20)
            return

        for reg_id, hora, tipo in filas:
            fila_frame = ctk.CTkFrame(self.scroll_auditoria, fg_color="#f8f9fa")
            fila_frame.pack(fill="x", pady=2, padx=5)
            
            ctk.CTkLabel(fila_frame, text=f"{hora} - {tipo}", font=("Helvetica", 14, "bold"), text_color="#333").pack(side="left", padx=15, pady=5)
            ctk.CTkButton(fila_frame, text="🗑️ Eliminar", fg_color="#dc3545", hover_color="#c82333", width=80,
                          command=lambda i=reg_id: self.eliminar_registro(i)).pack(side="right", padx=15, pady=5)

    def eliminar_registro(self, registro_id):
        confirm = messagebox.askyesno("Confirmar", "¿Eliminar permanentemente este registro?")
        if confirm:
            from src.models.db_manager import crear_conexion
            conn = crear_conexion()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM asistencia WHERE id=?", (registro_id,))
            conn.commit()
            conn.close()
            self.buscar_registros_asistencia() # Refrescar lista

    def insertar_registro_manual(self):
        empleado = self.cmb_empleado_auditoria.get()
        fecha = self.ent_fecha_auditoria.get()
        hora = self.ent_nueva_hora.get()
        tipo = self.cmb_nuevo_tipo.get()

        if not hora or len(hora.split(":")) < 2:
            messagebox.showwarning("Formato Inválido", "Ingresa una hora válida en formato HH:MM (ej. 14:30:00).")
            return

        from src.models.db_manager import crear_conexion
        conn = crear_conexion()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO asistencia (empleado_nombre, fecha, hora, tipo_registro, sucursal) 
            VALUES (?, ?, ?, ?, 'Auditoría Manual')
        """, (empleado, fecha, hora, tipo))
        conn.commit()
        conn.close()
        
        self.ent_nueva_hora.delete(0, 'end')
        self.buscar_registros_asistencia() # Refrescar lista

    # ==========================================
    # PESTAÑA 3: SISTEMA Y SEGURIDAD
    # ==========================================
    def _construir_tab_sistema(self):
        ctk.CTkLabel(self.tab_sistema, text="Opciones de Infraestructura", font=("Helvetica", 14, "bold")).pack(pady=20)
        ctk.CTkButton(self.tab_sistema, text="💾 Respaldar Base de Datos", width=250, command=self.accion_backup).pack(pady=10)
        ctk.CTkButton(self.tab_sistema, text="🔑 Cambiar PIN de Administrador", width=250, fg_color="#6c757d", command=self.accion_cambiar_pin).pack(pady=10)

    # --- Funciones Utilitarias (Mantenidas) ---
    def obtener_lista_empleados(self):
        try:
            from src.models.db_manager import crear_conexion
            conn = crear_conexion()
            cursor = conn.cursor()
            cursor.execute("SELECT nombre FROM empleados WHERE estatus = 'Activo'")
            lista = [row[0] for row in cursor.fetchall()]
            conn.close()
            return lista if lista else ["No hay empleados"]
        except: return ["Error de conexión"]

    def accion_cambiar_pin(self):
        # Lógica de cambio de PIN original
        pass

    def accion_backup(self):
        # Lógica de backup original
        pass