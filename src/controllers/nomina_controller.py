from datetime import datetime

class NominaController:
    
    @staticmethod
    def calcular_horas_transcurridas(entrada: datetime, salida: datetime) -> float:
        """
        Calcula el tiempo exacto trabajado en horas decimales.
        Soporta automáticamente turnos nocturnos gracias a los objetos datetime.
        """
        if not entrada or not salida:
            return 0.0
            
        diferencia = salida - entrada
        # Convertimos a horas exactas (ej. 8 horas y 15 min = 8.25 horas)
        horas_decimales = diferencia.total_seconds() / 3600.0
        
        # Evitar cálculos negativos si hay un error de captura
        return max(0.0, horas_decimales)

    @staticmethod
    def calcular_pago_neto(horas_trabajadas: float, pago_hora: float, 
                           total_comisiones_base: float, bonos: float, descuentos: float) -> dict:
        """
        Aplica la fórmula de nómina integrando pagos exactos por minuto y bases.
        """
        # Sueldo exacto (descuenta retrasos automáticamente al basarse en segundos totales)
        sueldo_tiempo = horas_trabajadas * pago_hora
        
        # Ecuación del pago final
        pago_neto = (sueldo_tiempo + total_comisiones_base + bonos) - descuentos
        
        return {
            "horas_calculadas": round(horas_trabajadas, 2),
            "sueldo_tiempo": round(sueldo_tiempo, 2),
            "comisiones_base": round(total_comisiones_base, 2),
            "bonos": round(bonos, 2),
            "descuentos": round(descuentos, 2),
            "pago_neto": round(pago_neto, 2)
        }