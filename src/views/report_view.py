import customtkinter as ctk
import os
import sys
from datetime import datetime

# Rutas para encontrar la configuración
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from config.theme import COLOR_PRIMARIO

class ReportView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="white", corner_radius=10)
        
        # Título del panel
        self.lbl_titulo = ctk.CTkLabel(self, text="NÓMINA SEMANAL Y CONTROL DE HORAS", font=("Helvetica", 18, "bold"), text_color=COLOR_PRIMARIO)
        self.lbl_titulo.pack(pady=(15, 5))

        # Definición de la semana actual (Lunes 13 a Domingo 19 de Abril 2026)
        self.fecha_inicio = "2026-04-13" 
        self.fecha_fin = "2026-04-19"
        
        self.lbl_info = ctk.CTkLabel(self, text=f"Período: del {self.fecha_inicio} al {self.fecha_fin}", font=("Helvetica", 12, "italic"))
        self.lbl_info.pack(pady=(0, 10))

        # Contenedor de la tabla con scroll
        self.tabla_frame = ctk.CTkScrollableFrame(self, height=350, orientation="horizontal", fg_color="#F2F2F2")
        self.tabla_frame.pack(fill="both", expand=True, padx=15, pady=15)

        self.cargar_datos_tabla()

    def cargar_datos_tabla(self):
        """Limpia y reconstruye la tabla con todos los empleados actuales."""
        for widget in self.tabla_frame.winfo_children():
            widget.destroy()

        # Configuración de anchos: Personal más ancho, días estándar
        headers = ["Personal", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo", "Total Hrs", "Sueldo Semanal"]
        anchos = [140, 90, 90, 90, 90, 90, 90, 90, 100, 130]
        
        for i, h in enumerate(headers):
            frame_h = ctk.CTkFrame(self.tabla_frame, fg_color=COLOR_PRIMARIO, corner_radius=0, width=anchos[i], height=40)
            frame_h.grid(row=0, column=i, padx=1, pady=1, sticky="nsew")
            frame_h.grid_propagate(False)
            lbl = ctk.CTkLabel(frame_h, text=h, font=("Helvetica", 11, "bold"), text_color="white")
            lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Consulta SQL: LEFT JOIN asegura que salgan TODOS los empleados aunque no tengan asistencia
        from src.models.db_manager import crear_conexion
        conn = crear_conexion()
        if not conn: return
        
        cursor = conn.cursor()
        query = """
            SELECT e.nombre, a.fecha, a.hora, a.tipo_registro, e.pago_hora
            FROM empleados e
            LEFT JOIN asistencia a ON e.nombre = a.empleado_nombre
                AND a.fecha BETWEEN ? AND ?
            WHERE e.estatus = 'Activo'
            ORDER BY e.nombre, a.fecha, a.hora
        """
        cursor.execute(query, (self.fecha_inicio, self.fecha_fin))
        filas = cursor.fetchall()
        conn.close()

        self.procesar_y_dibujar(filas, anchos)

    def procesar_y_dibujar(self, filas, anchos):
        """Organiza los datos horizontalmente y genera las celdas."""
        nomina = {}
        for nombre, fecha, hora, tipo, pago in filas:
            if nombre not in nomina:
                nomina[nombre] = {"dias": {i: [] for i in range(7)}, "pago": pago or 0.0}
            
            if fecha and hora:
                try:
                    dia_idx = datetime.strptime(fecha, "%Y-%m-%d").weekday()
                    nomina[nombre]["dias"][dia_idx].append(hora)
                except: pass

        fila_idx = 1
        for nombre, datos in nomina.items():
            # Columna Personal
            self._insertar_celda(fila_idx, 0, nombre, anchos[0], "bold")
            
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

            # Totales
            self._insertar_celda(fila_idx, 8, f"{horas_acumuladas:.2f} hrs", anchos[8], "bold")
            salario = horas_acumuladas * datos["pago"]
            self._insertar_celda(fila_idx, 9, f"${salario:,.2f}", anchos[9], "bold", "#006400")
            
            fila_idx += 1

    def _insertar_celda(self, f, c, txt, w, peso="normal", color="black"):
        bg = "white" if f % 2 == 0 else "#F9F9F9" # Efecto cebra para lectura fácil
        frame = ctk.CTkFrame(self.tabla_frame, fg_color=bg, corner_radius=0, width=w, height=35)
        frame.grid(row=f, column=c, padx=1, pady=1, sticky="nsew")
        frame.grid_propagate(False)
        lbl = ctk.CTkLabel(frame, text=txt, font=("Helvetica", 11, peso), text_color=color)
        lbl.place(relx=0.5, rely=0.5, anchor="center")