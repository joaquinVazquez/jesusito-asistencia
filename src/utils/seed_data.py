import os
import sys

# Apuntamos a la raíz para importar nuestros controladores
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from src.controllers.empleado_controller import registrar_empleado
from src.controllers.asistencia_controller import registrar_asistencia

def inyectar_lote_pruebas():
    """Puebla la base de datos con registros controlados para auditoría visual."""
    print("--- Iniciando Inyección de Datos Semilla ---")
    
    # 1. Alta de Catálogo de Empleados
    empleados_demo = ["Carlos Pastelero", "Ana Mostrador", "Luis Repartidor", "Sofía Gerente"]
    for emp in empleados_demo:
        registrar_empleado(emp)
        
    # 2. Simulación de un día operativo (14 de Abril de 2026)
    asistencias_demo = [
        ("Carlos Pastelero", "2026-04-14", "07:55", "Entrada"),
        ("Ana Mostrador", "2026-04-14", "08:02", "Entrada"),
        ("Luis Repartidor", "2026-04-14", "08:15", "Entrada"),
        ("Sofía Gerente", "2026-04-14", "09:00", "Entrada"),
        ("Carlos Pastelero", "2026-04-14", "16:05", "Salida"),
        ("Ana Mostrador", "2026-04-14", "16:10", "Salida"),
    ]
    
    registros_exitosos = 0
    for a in asistencias_demo:
        if registrar_asistencia(a[0], a[1], a[2], a[3]):
            registros_exitosos += 1
            
    print(f"\n[SISTEMA] Se inyectaron {registros_exitosos} registros exitosamente.")
    print("-> Siguiente paso: Ejecutar nuevamente el generador de PDF.")

if __name__ == "__main__":
    inyectar_lote_pruebas()