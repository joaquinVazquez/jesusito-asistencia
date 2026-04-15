import sqlite3
import os

DB_PATH = os.path.join("data", "jesusito_asistencia.db")

def simular():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Asegurar empleados con sueldos del Excel
    empleados = [('Doña Anita', 62.5), ('Bere', 25.0)]
    cursor.executemany("INSERT OR REPLACE INTO empleados (nombre, pago_hora) VALUES (?, ?)", empleados)

    # 2. Registros de prueba (Lunes 13 a Miércoles 15 de Abril 2026)
    asistencias = [
        # Doña Anita: 8 horas diarias
        ('Doña Anita', '2026-04-13', '08:00:00', 'Entrada'),
        ('Doña Anita', '2026-04-13', '16:00:00', 'Salida'),
        ('Doña Anita', '2026-04-14', '08:00:00', 'Entrada'),
        ('Doña Anita', '2026-04-14', '16:00:00', 'Salida'),
        # Bere: 7 horas diarias
        ('Bere', '2026-04-13', '08:00:00', 'Entrada'),
        ('Bere', '2026-04-13', '15:00:00', 'Salida'),
        ('Bere', '2026-04-14', '08:00:00', 'Entrada'),
        ('Bere', '2026-04-14', '15:00:00', 'Salida')
    ]
    cursor.executemany("INSERT INTO asistencia (empleado_nombre, fecha, hora, tipo_registro) VALUES (?, ?, ?, ?)", asistencias)
    
    conn.commit()
    conn.close()
    print("Simulación completada con éxito.")

if __name__ == "__main__":
    simular()