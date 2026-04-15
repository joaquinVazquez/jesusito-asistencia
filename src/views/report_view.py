import customtkinter as ctk
import os
import sys
from datetime import datetime # Importación limpia al inicio

# Rutas para encontrar la configuración
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from config.theme import COLOR_PRIMARIO

class ReportView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="white", corner_radius=10)
        
        # Título del panel
        self.lbl_titulo = ctk.CTkLabel(self, text="Vista Previa de Nómina Semanal", font=("Helvetica", 16, "bold"), text_color=COLOR_PRIMARIO)
        self.lbl_titulo.pack(pady=10)

        # Contenedor de la tabla con scroll
        self.tabla_frame = ctk.CTkScrollableFrame(self, height=250, orientation="horizontal", fg_color="transparent")
        self.tabla_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Rango de la semana
        self.fecha_inicio = "2026-04-13" 
        self.fecha_fin = "2026-04-19"
        
        self.lbl_info = ctk.CTkLabel(self, text=f"Semana: {self.fecha_inicio} al {self.fecha_fin}")
        self.lbl_info.pack(pady=5)
        
        self.cargar_datos_tabla()

    def cargar_datos_tabla(self):
        """Prepara la interfaz y ejecuta la consulta SQL de la semana."""
        for widget in self.tabla_frame.winfo_children():
            widget.destroy()

        # Encabezados
        headers = ["Personal", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo", "Hrs Totales", "Salario Semanal"]
        for i, h in enumerate(headers):
            frame_celda = ctk.CTkFrame(self.tabla_frame, fg_color="#E0E0E0", corner_radius=0, width=100, height=35)
            frame_celda.grid(row=0, column=i, padx=1, pady=1, sticky="nsew")
            frame_celda.grid_propagate(False)
            lbl = ctk.CTkLabel(frame_celda, text=h, font=("Helvetica", 10, "bold"), text_color="black")
            lbl.place(relx=0.5, rely=0.5, anchor="center")

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

        # Llamamos a la única definición válida de procesar_nomina
        self.procesar_nomina(filas)

    def procesar_nomina(self, filas):
        """Agrupa los registros por día, calcula horas y dibuja las filas."""
        nomina = {}
        for nombre, fecha, hora, tipo, pago in filas:
            if nombre not in nomina:
                nomina[nombre] = {"dias": {i: [] for i in range(7)}, "pago": pago or 0.0}

            if fecha and hora:
                try:
                    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
                    dia_semana = fecha_obj.weekday()
                    nomina[nombre]["dias"][dia_semana].append(hora)
                except: pass

        fila_ui = 1
        for nombre, datos in nomina.items():
            self._crear_celda(fila_ui, 0, nombre)
            
            total_horas_semana = 0.0

            for dia in range(7):
                horas_dia = 0.0
                registros = datos["dias"][dia]

                # Lógica: Necesita al menos una Entrada y una Salida para calcular
                if len(registros) >= 2:
                    hora_ent = registros[0]
                    hora_sal = registros[-1]
                    try:
                        t_ent = datetime.strptime(hora_ent, '%H:%M:%S')
                        t_sal = datetime.strptime(hora_sal, '%H:%M:%S')
                        tdelta = t_sal - t_ent
                        horas_dia = max(0, tdelta.total_seconds() / 3600.0)
                    except: pass
                
                total_horas_semana += horas_dia
                texto_dia = f"{horas_dia:.2f}" if horas_dia > 0 else "-"
                self._crear_celda(fila_ui, dia + 1, texto_dia)

            self._crear_celda(fila_ui, 8, f"{total_horas_semana:.2f}")
            salario = total_horas_semana * datos["pago"]
            self._crear_celda(fila_ui, 9, f"${salario:,.2f}", color_texto="#006400")

            fila_ui += 1

    def _crear_celda(self, fila, columna, texto, color_texto="black"):
        """Método auxiliar para construir celdas uniformes."""
        frame = ctk.CTkFrame(self.tabla_frame, fg_color="white", corner_radius=0, width=100, height=30)
        frame.grid(row=fila, column=columna, padx=1, pady=1, sticky="nsew")
        frame.grid_propagate(False)
        lbl = ctk.CTkLabel(frame, text=texto, font=("Helvetica", 11), text_color=color_texto)
        lbl.place(relx=0.5, rely=0.5, anchor="center")