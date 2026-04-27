import customtkinter as ctk
import os
import sys
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from config.theme import COLOR_PRIMARIO

class ReportView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="white", corner_radius=10)
        
        self.lbl_titulo = ctk.CTkLabel(self, text="NÓMINA SEMANAL Y CONTROL DE HORAS", font=("Helvetica", 18, "bold"), text_color=COLOR_PRIMARIO)
        self.lbl_titulo.pack(pady=(15, 5))

        # --- CONTROLES DE NAVEGACIÓN Y EXPORTACIÓN ---
        self.ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.ctrl_frame.pack(fill="x", padx=15, pady=5)

        self.btn_prev = ctk.CTkButton(self.ctrl_frame, text="◀ Semana Anterior", width=120, command=self.semana_anterior)
        self.btn_prev.pack(side="left")

        self.lbl_info = ctk.CTkLabel(self.ctrl_frame, text="", font=("Helvetica", 14, "bold"))
        self.lbl_info.pack(side="left", expand=True)

        self.btn_next = ctk.CTkButton(self.ctrl_frame, text="Semana Siguiente ▶", width=120, command=self.semana_siguiente)
        self.btn_next.pack(side="left")

        self.btn_exportar = ctk.CTkButton(self.ctrl_frame, text="📄 Exportar PDF", width=120, fg_color="#28a745", hover_color="#218838", command=self.exportar_pdf)
        self.btn_exportar.pack(side="right", padx=(20, 0))
        # ----------------------------------------------

        self.tabla_frame = ctk.CTkScrollableFrame(self, height=350, orientation="horizontal", fg_color="#F2F2F2")
        self.tabla_frame.pack(fill="both", expand=True, padx=15, pady=15)

        self.datos_exportacion = [] 
        
        # Pivote inicial (Ajustable a datetime.now() en producción)
        self.fecha_pivote = datetime(2026, 4, 13)
        self.actualizar_fechas()

    def semana_anterior(self):
        self.fecha_pivote -= timedelta(days=7)
        self.actualizar_fechas()

    def semana_siguiente(self):
        self.fecha_pivote += timedelta(days=7)
        self.actualizar_fechas()

    def actualizar_fechas(self):
        lunes = self.fecha_pivote - timedelta(days=self.fecha_pivote.weekday())
        domingo = lunes + timedelta(days=6)
        self.fecha_inicio = lunes.strftime("%Y-%m-%d")
        self.fecha_fin = domingo.strftime("%Y-%m-%d")
        
        self.lbl_info.configure(text=f"Período: {self.fecha_inicio} al {self.fecha_fin}")
        self.cargar_datos_tabla()

    def cargar_datos_tabla(self):
        for widget in self.tabla_frame.winfo_children():
            widget.destroy()

        # NUEVAS COLUMNAS Y ANCHOS AJUSTADOS (12 columnas en total)
        headers = ["Personal", "Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do", "Total Hrs", "Bonos", "Desc.", "Sueldo Neto"]
        anchos = [110, 60, 60, 60, 60, 60, 60, 60, 80, 80, 80, 100]
        
        for i, h in enumerate(headers):
            frame_h = ctk.CTkFrame(self.tabla_frame, fg_color=COLOR_PRIMARIO, corner_radius=0, width=anchos[i], height=40)
            frame_h.grid(row=0, column=i, padx=1, pady=1, sticky="nsew")
            frame_h.grid_propagate(False)
            lbl = ctk.CTkLabel(frame_h, text=h, font=("Helvetica", 11, "bold"), text_color="white")
            lbl.place(relx=0.5, rely=0.5, anchor="center")

        from src.models.db_manager import crear_conexion
        conn = crear_conexion()
        if not conn: return
        cursor = conn.cursor()

        # 1. Consultar Asistencia
        query_asistencia = """
            SELECT e.nombre, a.fecha, a.hora, a.tipo_registro, e.pago_hora
            FROM empleados e
            LEFT JOIN asistencia a ON e.nombre = a.empleado_nombre
                AND a.fecha BETWEEN ? AND ?
            WHERE e.estatus = 'Activo'
            ORDER BY e.nombre, a.fecha, a.hora
        """
        cursor.execute(query_asistencia, (self.fecha_inicio, self.fecha_fin))
        filas_asistencia = cursor.fetchall()

        # 2. Consultar Ajustes (Bonos y Descuentos del periodo seleccionado)
        query_ajustes = """
            SELECT empleado_nombre, tipo, SUM(monto) 
            FROM ajustes 
            WHERE fecha BETWEEN ? AND ? 
            GROUP BY empleado_nombre, tipo
        """
        cursor.execute(query_ajustes, (self.fecha_inicio, self.fecha_fin))
        filas_ajustes = cursor.fetchall()
        conn.close()

        # Crear diccionario de ajustes por empleado
        ajustes_dict = {}
        for nombre, tipo, total in filas_ajustes:
            if nombre not in ajustes_dict:
                ajustes_dict[nombre] = {"Bono": 0.0, "Descuento": 0.0}
            ajustes_dict[nombre][tipo] = total

        self.procesar_y_dibujar(filas_asistencia, ajustes_dict, anchos)

    def procesar_y_dibujar(self, filas_asistencia, ajustes_dict, anchos):
        self.datos_exportacion = [] 
        nomina = {}
        for nombre, fecha, hora, tipo, pago in filas_asistencia:
            if nombre not in nomina:
                nomina[nombre] = {"dias": {i: [] for i in range(7)}, "pago": pago or 0.0}
            
            if fecha and hora:
                try:
                    dia_idx = datetime.strptime(fecha, "%Y-%m-%d").weekday()
                    nomina[nombre]["dias"][dia_idx].append(hora)
                except: pass

        fila_idx = 1
        for nombre, datos in nomina.items():
            self._insertar_celda(fila_idx, 0, nombre, anchos[0], "bold")
            fila_matriz = [nombre] 
            horas_acumuladas = 0.0

            for dia in range(7):
                registros = datos["dias"][dia]
                hrs_dia = 0.0
                if len(registros) >= 2:
                    try:
                        t_ent = datetime.strptime(registros[0], '%H:%M:%S')
                        t_sal = datetime.strptime(registros[-1], '%H:%M:%S')
                        hrs_dia = (t_sal - t_ent).total_seconds() / 3600.0
                    except: pass
                
                horas_acumuladas += hrs_dia
                texto_dia = f"{hrs_dia:.2f}" if hrs_dia > 0 else "-"
                self._insertar_celda(fila_idx, dia + 1, texto_dia, anchos[dia+1])
                fila_matriz.append(texto_dia)

            # LÓGICA FINANCIERA
            bono = ajustes_dict.get(nombre, {}).get("Bono", 0.0)
            desc = ajustes_dict.get(nombre, {}).get("Descuento", 0.0)
            salario_base = horas_acumuladas * datos["pago"]
            salario_neto = salario_base + bono - desc

            # Rellenar UI con Horas, Bono, Descuento y Neto
            self._insertar_celda(fila_idx, 8, f"{horas_acumuladas:.2f}", anchos[8], "bold")
            self._insertar_celda(fila_idx, 9, f"${bono:,.2f}", anchos[9], "normal", "blue")
            self._insertar_celda(fila_idx, 10, f"-${desc:,.2f}", anchos[10], "normal", "red")
            self._insertar_celda(fila_idx, 11, f"${salario_neto:,.2f}", anchos[11], "bold", "#006400")
            
            # Guardar en matriz para PDF
            fila_matriz.extend([f"{horas_acumuladas:.2f}", f"${bono:,.2f}", f"${desc:,.2f}", f"${salario_neto:,.2f}"])
            self.datos_exportacion.append(fila_matriz)
            
            fila_idx += 1

    def _insertar_celda(self, f, c, txt, w, peso="normal", color="black"):
        bg = "white" if f % 2 == 0 else "#F9F9F9"
        frame = ctk.CTkFrame(self.tabla_frame, fg_color=bg, corner_radius=0, width=w, height=35)
        frame.grid(row=f, column=c, padx=1, pady=1, sticky="nsew")
        frame.grid_propagate(False)
        lbl = ctk.CTkLabel(frame, text=txt, font=("Helvetica", 11, peso), text_color=color)
        lbl.place(relx=0.5, rely=0.5, anchor="center")

    def exportar_pdf(self):
        ruta_destino = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"Nomina_{self.fecha_inicio}_al_{self.fecha_fin}.pdf",
            filetypes=[("Archivos PDF", "*.pdf")],
            title="Guardar Reporte Semanal"
        )
        if ruta_destino:
            from src.utils.pdf_generator import generar_pdf_nomina
            exito = generar_pdf_nomina(ruta_destino, self.fecha_inicio, self.fecha_fin, self.datos_exportacion)
            if exito:
                messagebox.showinfo("Éxito", "Reporte PDF generado y abierto correctamente.")
            else:
                messagebox.showerror("Error", "No se pudo generar el reporte. Verifica que el archivo no esté abierto.")