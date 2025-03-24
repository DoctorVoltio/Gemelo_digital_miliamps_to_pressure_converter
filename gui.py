import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import random
import math

class ConvertidorIP_DigitalTwin:
    def __init__(self):
        self.rango_entrada_nominal = (4.0, 20.0)
        self.rango_salida_nominal = (3.0, 15.0)
        self.zero_error = 0.0
        self.span_error = 0.0
        self.zero_ajuste = 0.0
        self.span_ajuste = 1.0
        self.tiempo_respuesta = 0.5
        self.presion_actual = 3.0
        self.ruido = 0.05
        self.deriva = 0.01
        self.ultima_actualizacion = time.time()
    
    def actualizar(self, corriente_entrada):
        corriente = max(self.rango_entrada_nominal[0], min(self.rango_entrada_nominal[1], corriente_entrada))
        ahora = time.time()
        dt = ahora - self.ultima_actualizacion
        self.ultima_actualizacion = ahora
        
        zero_real = self.rango_salida_nominal[0] + self.zero_error + self.zero_ajuste
        span_nominal = (self.rango_salida_nominal[1] - self.rango_salida_nominal[0])
        pendiente_nominal = span_nominal / (self.rango_entrada_nominal[1] - self.rango_entrada_nominal[0])
        presion_objetivo = zero_real + (corriente - self.rango_entrada_nominal[0]) * (
            pendiente_nominal * (1 + self.span_error/100) * self.span_ajuste)
        
        tau = self.tiempo_respuesta
        alpha = math.exp(-dt/tau)
        self.presion_actual = alpha * self.presion_actual + (1 - alpha) * presion_objetivo
        self.presion_actual += random.gauss(0, self.ruido)
        self.presion_actual += (self.deriva / 3600) * dt
        self.presion_actual = max(2.0, min(16.0, self.presion_actual))
        return self.presion_actual
    
    def calibrar_zero(self, valor_real):
        self.zero_ajuste = valor_real - self.rango_salida_nominal[0] - self.zero_error
    
    def calibrar_span(self, valor_real):
        span_actual = valor_real - (self.rango_salida_nominal[0] + self.zero_error + self.zero_ajuste)
        span_nominal = self.rango_salida_nominal[1] - self.rango_salida_nominal[0]
        self.span_ajuste = span_actual / (span_nominal * (1 + self.span_error/100))
    
    def set_zero_error(self, error):
        self.zero_error = error
    
    def set_span_error(self, error_porcentaje):
        self.span_error = error_porcentaje

class IPConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemelo Digital - Convertidor I/P")
        self.root.geometry("1000x700")
        self.convertidor = ConvertidorIP_DigitalTwin()
        self.historial = {'tiempo': [], 'corriente': [], 'presion': []}
        self.en_ejecucion = False
        self.crear_widgets()
        self.actualizar_grafico()
    
    def crear_widgets(self):
        control_frame = ttk.LabelFrame(self.root, text="Controles", padding=10)
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ttk.Label(control_frame, text="Corriente de entrada (mA):").grid(row=0, column=0, sticky="w")
        self.corriente_slider = ttk.Scale(control_frame, from_=4.0, to=20.0, length=300, command=self.actualizar_corriente)
        self.corriente_slider.set(4.0)
        self.corriente_slider.grid(row=1, column=0, columnspan=2, pady=5)
        
        self.corriente_entry = ttk.Entry(control_frame, width=8)
        self.corriente_entry.insert(0, "4.0")
        self.corriente_entry.grid(row=1, column=2, padx=5)
        self.corriente_entry.bind("<Return>", self.actualizar_desde_entry)
        
        ttk.Label(control_frame, text="Presión de salida (psi):").grid(row=2, column=0, sticky="w", pady=(10,0))
        self.presion_label = ttk.Label(control_frame, text="3.00", font=('Arial', 14, 'bold'))
        self.presion_label.grid(row=3, column=0, columnspan=3, pady=5)
        
        ttk.Button(control_frame, text="Iniciar Simulación", command=self.iniciar_simulacion).grid(row=4, column=0, pady=10)
        ttk.Button(control_frame, text="Detener", command=self.detener_simulacion).grid(row=4, column=1, pady=10)
        ttk.Button(control_frame, text="Resetear", command=self.resetear_sistema).grid(row=4, column=2, pady=10)
        
        calib_frame = ttk.LabelFrame(control_frame, text="Calibración", padding=10)
        calib_frame.grid(row=5, column=0, columnspan=3, pady=10, sticky="ew")
        
        ttk.Label(calib_frame, text="Error Zero (psi):").grid(row=0, column=0, sticky="w")
        self.zero_error_entry = ttk.Entry(calib_frame, width=8)
        self.zero_error_entry.insert(0, "0.0")
        self.zero_error_entry.grid(row=0, column=1, sticky="w")
        
        ttk.Label(calib_frame, text="Error Span (%):").grid(row=1, column=0, sticky="w")
        self.span_error_entry = ttk.Entry(calib_frame, width=8)
        self.span_error_entry.insert(0, "0.0")
        self.span_error_entry.grid(row=1, column=1, sticky="w")
        
        ttk.Button(calib_frame, text="Aplicar Errores", command=self.aplicar_errores).grid(row=2, column=0, columnspan=2, pady=5)
        
        ttk.Label(calib_frame, text="Ajuste Zero @4mA:").grid(row=3, column=0, sticky="w", pady=(10,0))
        self.calib_zero_entry = ttk.Entry(calib_frame, width=8)
        self.calib_zero_entry.insert(0, "3.0")
        self.calib_zero_entry.grid(row=3, column=1, sticky="w")
        
        ttk.Button(calib_frame, text="Ajustar Zero", command=self.ajustar_zero).grid(row=4, column=0, columnspan=2, pady=5)
        
        ttk.Label(calib_frame, text="Ajuste Span @20mA:").grid(row=5, column=0, sticky="w", pady=(10,0))
        self.calib_span_entry = ttk.Entry(calib_frame, width=8)
        self.calib_span_entry.insert(0, "15.0")
        self.calib_span_entry.grid(row=5, column=1, sticky="w")
        
        ttk.Button(calib_frame, text="Ajustar Span", command=self.ajustar_span).grid(row=6, column=0, columnspan=2, pady=5)
        
        self.fig, self.ax = plt.subplots(figsize=(10, 5))
        self.linea_presion, = self.ax.plot([], [], 'b-', label='Presión (psi)')
        self.linea_corriente, = self.ax.plot([], [], 'r--', label='Corriente (mA)')
        self.ax.set_xlabel('Tiempo (s)')
        self.ax.set_ylabel('Valor')
        self.ax.legend()
        self.ax.grid(True)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
    
    def actualizar_corriente(self, valor):
        corriente = float(valor)
        self.corriente_entry.delete(0, tk.END)
        self.corriente_entry.insert(0, f"{corriente:.2f}")
        
        if not self.en_ejecucion:
            presion = self.convertidor.actualizar(corriente)
            self.actualizar_indicadores(corriente, presion)

    def actualizar_desde_entry(self, event):
        try:
            corriente = float(self.corriente_entry.get())
            corriente = max(4.0, min(20.0, corriente))
            self.corriente_slider.set(corriente)
            self.corriente_entry.delete(0, tk.END)
            self.corriente_entry.insert(0, f"{corriente:.2f}")
            
            if not self.en_ejecucion:
                presion = self.convertidor.actualizar(corriente)
                self.actualizar_indicadores(corriente, presion)
        except ValueError:
            pass

    def aplicar_errores(self):
        try:
            zero_error = float(self.zero_error_entry.get())
            span_error = float(self.span_error_entry.get())
            self.convertidor.set_zero_error(zero_error)
            self.convertidor.set_span_error(span_error)
        except ValueError:
            pass

    def ajustar_zero(self):
        try:
            valor_deseado = float(self.calib_zero_entry.get())
            self.convertidor.calibrar_zero(valor_deseado)
        except ValueError:
            pass

    def ajustar_span(self):
        try:
            valor_deseado = float(self.calib_span_entry.get())
            self.convertidor.calibrar_span(valor_deseado)
        except ValueError:
            pass

    def iniciar_simulacion(self):
        if not self.en_ejecucion:
            self.en_ejecucion = True
            self.tiempo_inicio = time.time()
            self.historial = {'tiempo': [], 'corriente': [], 'presion': []}
            self.simular()

    def simular(self):
        if self.en_ejecucion:
            corriente = float(self.corriente_slider.get())
            presion = self.convertidor.actualizar(corriente)
            self.actualizar_indicadores(corriente, presion)
            self.root.after(100, self.simular)

    def actualizar_indicadores(self, corriente, presion):
        self.presion_label.config(text=f"{presion:.2f}")
        tiempo_actual = time.time() - self.tiempo_inicio if hasattr(self, 'tiempo_inicio') else 0
        self.historial['tiempo'].append(tiempo_actual)
        self.historial['corriente'].append(corriente)
        self.historial['presion'].append(presion)
        
        if len(self.historial['tiempo']) > 100:
            for key in self.historial:
                self.historial[key] = self.historial[key][-100:]

    def actualizar_grafico(self):
        if self.historial['tiempo']:
            self.linea_presion.set_data(self.historial['tiempo'], self.historial['presion'])
            self.linea_corriente.set_data(self.historial['tiempo'], self.historial['corriente'])
            self.ax.relim()
            self.ax.autoscale_view()
            if len(self.historial['tiempo']) > 1:
                tiempo_max = max(self.historial['tiempo'])
                self.ax.set_xlim(max(0, tiempo_max - 20), max(20, tiempo_max))
            self.canvas.draw()
        self.root.after(100, self.actualizar_grafico)

    def detener_simulacion(self):
        self.en_ejecucion = False

    def resetear_sistema(self):
        self.convertidor = ConvertidorIP_DigitalTwin()
        self.historial = {'tiempo': [], 'corriente': [], 'presion': []}
        self.corriente_slider.set(4.0)
        self.corriente_entry.delete(0, tk.END)
        self.corriente_entry.insert(0, "4.0")
        self.presion_label.config(text="3.00")
        self.en_ejecucion = False

if __name__ == "__main__":
    root = tk.Tk()
    app = IPConverterGUI(root)
    root.mainloop()