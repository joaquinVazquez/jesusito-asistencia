import sqlite3
import os

DB_PATH = os.path.join("data", "jesusito_asistencia.db")

def poblar_datos_reales():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Limpiamos las tablas de pruebas anteriores
    cursor.execute("DELETE FROM asistencia")
    cursor.execute("DELETE FROM empleados")

    # 2. Catálogo real de empleados y Costo por hora
    empleados = [
        ('Doña Anita', 62.5), ('Rubi', 25.0), ('Meli', 25.0), ('Mariana', 25.0),
        ('Monica', 25.0), ('Bere', 25.0), ('MARI', 25.0), ('ELENA', 25.0),
        ('YOSE', 25.0), ('EVA', 25.0), ('SAMUEL', 25.0), ('TOÑO', 35.41)
    ]
    cursor.executemany("INSERT INTO empleados (nombre, pago_hora) VALUES (?, ?)", empleados)

    # 3. Mapeo de fechas para que coincida con la semana visible en tu sistema
    fechas = ['2026-04-13', '2026-04-14', '2026-04-15', '2026-04-16', '2026-04-17', '2026-04-18', '2026-04-19']

    # Estructura: Nombre, Lunes, Martes, Miércoles, Jueves, Viernes, Sábado, Domingo
    horarios = [
        ('Doña Anita', ('08:00:00', '16:00:00'), ('08:00:00', '16:00:00'), ('08:00:00', '16:00:00'), ('08:00:00', '16:00:00'), ('08:00:00', '16:00:00'), ('08:00:00', '16:00:00'), None),
        ('Rubi', ('08:00:00', '15:00:00'), ('08:00:00', '15:00:00'), ('08:00:00', '15:00:00'), ('08:00:00', '15:00:00'), ('08:00:00', '15:00:00'), ('08:00:00', '15:00:00'), None),
        ('Meli', ('08:00:00', '15:00:00'), ('08:00:00', '15:00:00'), None, ('08:00:00', '15:00:00'), ('08:00:00', '15:00:00'), ('05:00:00', '13:00:00'), None),
        ('Mariana', ('08:00:00', '15:00:00'), ('08:00:00', '15:00:00'), None, ('08:00:00', '15:00:00'), ('08:00:00', '15:00:00'), ('05:00:00', '13:00:00'), None),
        ('Monica', ('08:00:00', '15:00:00'), None, ('08:00:00', '15:00:00'), ('08:00:00', '15:00:00'), ('08:00:00', '15:00:00'), ('08:00:00', '15:00:00'), ('05:00:00', '13:00:00')),
        ('Bere', ('08:00:00', '15:00:00'), None, ('08:00:00', '15:00:00'), ('08:00:00', '15:00:00'), ('08:00:00', '15:00:00'), ('08:00:00', '15:00:00'), ('05:00:00', '13:00:00')),
        ('MARI', None, ('08:00:00', '15:00:00'), ('08:00:00', '15:00:00'), ('08:00:00', '16:00:00'), ('14:00:00', '21:00:00'), ('14:00:00', '21:00:00'), ('08:00:00', '21:00:00')),
        ('ELENA', ('08:00:00', '21:00:00'), ('14:00:00', '21:00:00'), ('14:00:00', '21:00:00'), ('14:00:00', '21:00:00'), ('14:00:00', '21:00:00'), ('14:00:00', '21:00:00'), None),
        ('YOSE', ('08:00:00', '16:00:00'), ('08:00:00', '16:00:00'), ('08:00:00', '16:00:00'), ('08:00:00', '16:00:00'), ('08:00:00', '16:00:00'), None, ('12:00:00', '20:00:00')),
        ('EVA', ('12:00:00', '20:00:00'), ('12:00:00', '20:00:00'), ('12:00:00', '20:00:00'), ('14:00:00', '21:00:00'), ('12:00:00', '20:00:00'), ('08:00:00', '20:00:00'), ('08:00:00', '16:00:00')),
        ('SAMUEL', None, None, None, None, None, None, None), # Samuel no tiene registros esta semana
        ('TOÑO', ('08:00:00', '15:30:00'), ('08:00:00', '16:30:00'), ('08:00:00', '15:30:00'), ('08:00:00', '17:00:00'), ('08:00:00', '16:00:00'), ('08:00:00', '19:00:00'), None)
    ]

    asistencias = []
    for datos in horarios:
        nombre = datos[0]
        dias = datos[1:]
        for i, horario_dia in enumerate(dias):
            if horario_dia is not None:
                entrada, salida = horario_dia
                fecha_str = fechas[i]
                # Inyectamos Entrada y Salida para que el motor matemático calcule las horas
                asistencias.append((nombre, fecha_str, entrada, 'Entrada'))
                asistencias.append((nombre, fecha_str, salida, 'Salida'))

    cursor.executemany("INSERT INTO asistencia (empleado_nombre, fecha, hora, tipo_registro) VALUES (?, ?, ?, ?)", asistencias)
    
    conn.commit()
    conn.close()
    print("[ÉXITO] 12 Empleados y sus horarios reales importados a la base de datos.")

if __name__ == "__main__":
    poblar_datos_reales()