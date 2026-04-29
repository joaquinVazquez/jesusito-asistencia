import customtkinter as ctk
from tkinter import messagebox
from src.models.db_manager import ejecutar_query

class ConfigFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="white", corner_radius=10)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        tabview = ctk.CTkTabview(self, fg_color="#f8f9fa")
        tabview.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        self.tab_sucursales = tabview.add("Gestión de Sucursales")
        self.tab_seguridad = tabview.add("Seguridad (Super Admin)")

        self._construir_sucursales()
        self._construir_seguridad()

    def _construir_sucursales(self):
        frame_form = ctk.CTkFrame(self.tab_sucursales, fg_color="transparent")
        frame_form.pack(pady=20)

        ctk.CTkLabel(frame_form, text="Nombre de Sucursal:", font=("Helvetica", 12, "bold")).grid(row=0, column=0, padx=10)
        self.ent_nombre_sucursal = ctk.CTkEntry(frame_form, width=200)
        self.ent_nombre_sucursal.grid(row=0, column=1, padx=10)

        ctk.CTkButton(frame_form, text="➕ Agregar", fg_color="#28a745", command=self.guardar_sucursal).grid(row=0, column=2, padx=20)

        self.scroll_sucursales = ctk.CTkScrollableFrame(self.tab_sucursales, fg_color="#ffffff", height=200)
        self.scroll_sucursales.pack(fill="x", padx=50, pady=10)
        self.cargar_sucursales()

    def cargar_sucursales(self):
        for w in self.scroll_sucursales.winfo_children(): w.destroy()
        sucursales = ejecutar_query("SELECT id, nombre FROM sucursales ORDER BY id", fetch=True)
        if sucursales:
            for s in sucursales:
                f = ctk.CTkFrame(self.scroll_sucursales, fg_color="#f1f1f1")
                f.pack(fill="x", pady=2)
                ctk.CTkLabel(f, text=f"📍 {s['nombre']}", font=("Helvetica", 12)).pack(side="left", padx=15, pady=5)

    def guardar_sucursal(self):
        nombre = self.ent_nombre_sucursal.get().strip()
        if not nombre: return
        exito = ejecutar_query("INSERT INTO sucursales (nombre) VALUES (%s)", (nombre,))
        if exito is True:
            self.ent_nombre_sucursal.delete(0, 'end')
            self.cargar_sucursales()
            messagebox.showinfo("Éxito", "Sucursal añadida al ecosistema.")

    def _construir_seguridad(self):
        frame_form = ctk.CTkFrame(self.tab_seguridad, fg_color="transparent")
        frame_form.pack(pady=50)

        ctk.CTkLabel(frame_form, text="Nuevo PIN de Acceso:", font=("Helvetica", 14, "bold")).pack(pady=10)
        self.ent_nuevo_pin = ctk.CTkEntry(frame_form, width=200, show="*", justify="center", font=("Helvetica", 18))
        self.ent_nuevo_pin.pack(pady=10)

        ctk.CTkButton(frame_form, text="💾 Actualizar PIN", fg_color="#e74c3c", command=self.actualizar_pin).pack(pady=20)

    def actualizar_pin(self):
        nuevo_pin = self.ent_nuevo_pin.get().strip()
        if len(nuevo_pin) < 4: return
        exito = ejecutar_query("UPDATE config SET valor = %s WHERE parametro = 'pin_admin'", (nuevo_pin,))
        if exito is True:
            messagebox.showinfo("Éxito", "PIN actualizado en la nube.")
            self.ent_nuevo_pin.delete(0, 'end')