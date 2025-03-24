class ConvertidorIP_DigitalTwin:
    def __init__(self):
        # Parámetros nominales
        self.rango_entrada_nominal = (4.0, 20.0)  # mA
        self.rango_salida_nominal = (3.0, 15.0)   # psi
        
        # Parámetros reales (con errores)
        self.zero_error = 0.0  # psi (error en punto cero)
        self.span_error = 0.0  # % (error en span)
        
        # Ajustes de calibración
        self.zero_ajuste = 0.0  # psi
        self.span_ajuste = 1.0  # factor
        
        # Otros parámetros
        self.tiempo_respuesta = 0.5
        self.presion_actual = 3.0
        self.ruido = 0.05
        self.deriva = 0.01  # psi/hora
        
    def actualizar(self, corriente_entrada):
        # Validar entrada
        corriente = max(self.rango_entrada_nominal[0], 
                       min(self.rango_entrada_nominal[1], corriente_entrada))
        
        # Calcular valor ideal sin errores
        span_nominal = (self.rango_salida_nominal[1] - self.rango_salida_nominal[0])
        pendiente_nominal = span_nominal / (self.rango_entrada_nominal[1] - self.rango_entrada_nominal[0])
        
        # Aplicar errores de zero y span
        zero_real = self.rango_salida_nominal[0] + self.zero_error + self.zero_ajuste
        span_real = span_nominal * (1 + self.span_error/100) * self.span_ajuste
        
        # Calcular presión objetivo con errores y ajustes
        presion_objetivo = zero_real + (corriente - self.rango_entrada_nominal[0]) * (
            pendiente_nominal * (1 + self.span_error/100) * self.span_ajuste)
        
        # Simular dinámica del sistema
        # [...] (misma implementación dinámica previa)
        
        return self.presion_actual
    
    def calibrar_zero(self, valor_real):
        """Ajusta el zero para que con 4mA se obtenga el valor_real"""
        self.zero_ajuste = valor_real - self.rango_salida_nominal[0] - self.zero_error
    
    def calibrar_span(self, valor_real):
        """Ajusta el span para que con 20mA se obtenga el valor_real"""
        span_actual = valor_real - (self.rango_salida_nominal[0] + self.zero_error + self.zero_ajuste)
        span_nominal = self.rango_salida_nominal[1] - self.rango_salida_nominal[0]
        self.span_ajuste = span_actual / (span_nominal * (1 + self.span_error/100))
    
    def set_zero_error(self, error):
        """Establece un error de zero simulado"""
        self.zero_error = error
    
    def set_span_error(self, error_porcentaje):
        """Establece un error de span simulado (% del span nominal)"""
        self.span_error = error_porcentaje