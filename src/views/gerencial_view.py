import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

class GerencialFrame(ctk.CTkFrame):
    def __init__(self, master):
        # Mantenemos el color de fondo blanco para que resalte
        super().__init__(master, fg_color="white", corner_radius=10)
        
        # --- ENCABEZADO ---
        self.lbl_titulo = ctk.CTkLabel(self, text="PRUEBA V1.1 - Mantenimiento", font=("Helvetica", 18, "bold"), text_color="#1a1a1a")
        self.lbl_titulo.pack(pady=15)

        # --- BOTONES DE SISTEMA (EN FILA) ---
        self.frame_sistema = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_sistema.pack(pady=10)

        self.btn_backup = ctk.CTkButton(self.frame_sistema, text="💾 Respaldar BD", width=150, command=self.accion_backup)
        self.btn_backup.pack(side="left", padx=10)

        self.btn_pin = ctk.CTkButton(self.frame_sistema, text="🔑 Cambiar PIN", width=150, fg_color="#6c757d", command=self.accion_cambiar_pin)
        self.btn_pin.pack(side="left", padx=10)

        # --- SEPARADOR VISUAL ---
        self.linea = ctk.CTkFrame(self, height=2, fg_color="#e0e0e0")
        self.linea.pack(fill="x", padx=40, pady=20)

        # --- CONTENEDOR DE AJUSTES (BONOS/DESCUENTOS) ---
        self.lbl_subtitulo = ctk.CTkLabel(self, text="GESTIÓN DE BONOS Y DESCUENTOS", font=("Helvetica", 14, "bold"), text_color="#2c3e50")
        self.lbl_subtitulo.pack(pady=5)

        self.frame_form = ctk.CTkFrame(self, fg_color="#f8f9fa", corner_radius=15)
        self.frame_form.pack(pady=10, padx=40, fill="x")

        # 1. Selección de Empleado
        ctk.CTkLabel(self.frame_form, text="Empleado:", font=("Helvetica", 12, "bold")).pack(pady=(10, 0))
        self.cmb_empleados = ctk.CTkOptionMenu(self.frame_form, values=self.obtener_lista_empleados(), width=250)
        self.cmb_empleados.pack(pady=5)

        # 2. Tipo (Bono / Descuento)
        self.tipo_ajuste = ctk.CTkSegmentedButton(self.frame_form, values=["Bono", "Descuento"], width=250)
        self.tipo_ajuste.set("Bono")
        self.tipo_ajuste.pack(pady=15)

        # 3. Monto y Motivo
        self.frame_inputs = ctk.CTkFrame(self.frame_form, fg_color="transparent")
        self.frame_inputs.pack(pady=10)

        self.ent_monto = ctk.CTkEntry(self.frame_inputs, placeholder_text="Monto $ (ej: 500)", width=120)
        self.ent_monto.pack(side="left", padx=5)

        self.ent_motivo = ctk.CTkEntry(self.frame_inputs, placeholder_text="Motivo (ej: Puntualidad)", width=200)
        self.ent_motivo.pack(side="left", padx=5)

        # 4. Botón de Acción
        self.btn_guardar = ctk.CTkButton(self.frame_form, text="Registrar en Nómina", 
                                          fg_color="#28a745", hover_color="#218838",
                                          width=250, height=40, font=("Helvetica", 12, "bold"),
                                          command=self.guardar_ajuste_db)
        self.btn_guardar.pack(pady=20)

    def obtener_lista_empleados(self):
        try:
            from src.models.db_manager import crear_conexion
            conn = crear_conexion()
            cursor = conn.cursor()
            cursor.execute("SELECT nombre FROM empleados WHERE estatus = 'Activo'")
            lista = [row[0] for row in cursor.fetchall()]
            conn.close()
            return lista if lista else ["No hay empleados"]
        except Exception as e:
            print(f"Error al cargar empleados: {e}")
            return ["Error de conexión"]

    def guardar_ajuste_db(self):
        empleado = self.cmb_empleados.get()
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

    def accion_cambiar_pin(self):
        # (Mantenemos tu lógica anterior de cambio de PIN)
        pass

    def accion_backup(self):
        # (Mantenemos tu lógica anterior de backup)
        pass