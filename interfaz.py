import tkinter as tk
from tkinter import ttk, messagebox
import random

class SolarRadiationPredictor:
    def __init__(self, root):
        self.root = root
        self.root.title("Predictor de Radiación Solar - Panamá")
        self.root.geometry("600x700")
        self.root.configure(bg='#f0f8ff')
        
        # Límites de Panamá
        self.PANAMA_BOUNDS = {
            'min_lat': 7.0,
            'max_lat': 9.7,
            'min_lon': -83.0,
            'max_lon': -77.0
        }
        
        self.create_widgets()
        
    def create_widgets(self):
        # Header Frame
        header_frame = tk.Frame(self.root, bg='#0066cc', pady=20)
        header_frame.pack(fill='x')
        
        title_label = tk.Label(
            header_frame,
            text="☀ Predictor de Radiación Solar",
            font=('Arial', 20, 'bold'),
            bg='#0066cc',
            fg='white'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text="Sistema de Predicción mediante Red Neuronal",
            font=('Arial', 11),
            bg='#0066cc',
            fg='white'
        )
        subtitle_label.pack()
        
        program_label = tk.Label(
            header_frame,
            text="Samsung Innovation Campus 2025 | Región de Panamá",
            font=('Arial', 9),
            bg='#0066cc',
            fg='#e0e0e0'
        )
        program_label.pack(pady=(5, 0))
        
        # Main Frame
        main_frame = tk.Frame(self.root, bg='#ffffff', padx=30, pady=30)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Instrucciones
        instruc_label = tk.Label(
            main_frame,
            text="Ingrese las coordenadas geográficas:",
            font=('Arial', 12, 'bold'),
            bg='#ffffff',
            fg='#333333'
        )
        instruc_label.pack(pady=(0, 20))
        
        # Latitud Frame
        lat_frame = tk.Frame(main_frame, bg='#ffffff')
        lat_frame.pack(fill='x', pady=10)
        
        lat_label = tk.Label(
            lat_frame,
            text="📍 Latitud (°):",
            font=('Arial', 11, 'bold'),
            bg='#ffffff',
            fg='#333333'
        )
        lat_label.pack(anchor='w')
        
        self.lat_entry = tk.Entry(
            lat_frame,
            font=('Arial', 12),
            relief='solid',
            bd=2,
            width=30
        )
        self.lat_entry.pack(fill='x', pady=(5, 0))
        self.lat_entry.insert(0, "Ej: 8.9824")
        self.lat_entry.bind('<FocusIn>', lambda e: self.clear_placeholder(self.lat_entry, "Ej: 8.9824"))
        self.lat_entry.bind('<FocusOut>', lambda e: self.restore_placeholder(self.lat_entry, "Ej: 8.9824"))
        
        lat_range = tk.Label(
            lat_frame,
            text=f"Rango válido: {self.PANAMA_BOUNDS['min_lat']}° a {self.PANAMA_BOUNDS['max_lat']}°",
            font=('Arial', 8),
            bg='#ffffff',
            fg='#666666'
        )
        lat_range.pack(anchor='w', pady=(2, 0))
        
        # Longitud Frame
        lon_frame = tk.Frame(main_frame, bg='#ffffff')
        lon_frame.pack(fill='x', pady=10)
        
        lon_label = tk.Label(
            lon_frame,
            text="📍 Longitud (°):",
            font=('Arial', 11, 'bold'),
            bg='#ffffff',
            fg='#333333'
        )
        lon_label.pack(anchor='w')
        
        self.lon_entry = tk.Entry(
            lon_frame,
            font=('Arial', 12),
            relief='solid',
            bd=2,
            width=30
        )
        self.lon_entry.pack(fill='x', pady=(5, 0))
        self.lon_entry.insert(0, "Ej: -79.5199")
        self.lon_entry.bind('<FocusIn>', lambda e: self.clear_placeholder(self.lon_entry, "Ej: -79.5199"))
        self.lon_entry.bind('<FocusOut>', lambda e: self.restore_placeholder(self.lon_entry, "Ej: -79.5199"))
        
        lon_range = tk.Label(
            lon_frame,
            text=f"Rango válido: {self.PANAMA_BOUNDS['min_lon']}° a {self.PANAMA_BOUNDS['max_lon']}°",
            font=('Arial', 8),
            bg='#ffffff',
            fg='#666666'
        )
        lon_range.pack(anchor='w', pady=(2, 0))
        
        # Buttons Frame
        button_frame = tk.Frame(main_frame, bg='#ffffff')
        button_frame.pack(pady=30)
        
        predict_btn = tk.Button(
            button_frame,
            text="🔮 Predecir Radiación Solar",
            font=('Arial', 12, 'bold'),
            bg='#0066cc',
            fg='white',
            activebackground='#0052a3',
            activeforeground='white',
            relief='raised',
            bd=3,
            padx=20,
            pady=10,
            command=self.predict_radiation,
            cursor='hand2'
        )
        predict_btn.pack(side='left', padx=5)
        
        clear_btn = tk.Button(
            button_frame,
            text="🗑 Limpiar",
            font=('Arial', 12),
            bg='#e0e0e0',
            fg='#333333',
            activebackground='#d0d0d0',
            activeforeground='#333333',
            relief='raised',
            bd=3,
            padx=20,
            pady=10,
            command=self.clear_fields,
            cursor='hand2'
        )
        clear_btn.pack(side='left', padx=5)
        
        # Results Frame
        self.result_frame = tk.Frame(main_frame, bg='#fffacd', relief='solid', bd=2)
        self.result_frame.pack(fill='both', expand=True, pady=20)
        self.result_frame.pack_forget()  # Ocultar inicialmente
        
        # Footer Frame
        footer_frame = tk.Frame(self.root, bg='#f0f8ff', pady=15)
        footer_frame.pack(fill='x', side='bottom')
        
        team_label = tk.Label(
            footer_frame,
            text="Equipo: Alan Sánchez, Abdiel Bernal, Ernesto Jurado, Ana Flores",
            font=('Arial', 9),
            bg='#f0f8ff',
            fg='#333333'
        )
        team_label.pack()
        
        project_label = tk.Label(
            footer_frame,
            text="Proyecto Final - Módulo Inteligencia Artificial | SIC 2025",
            font=('Arial', 8),
            bg='#f0f8ff',
            fg='#666666'
        )
        project_label.pack()
    
    def clear_placeholder(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg='#000000')
    
    def restore_placeholder(self, entry, placeholder):
        if entry.get() == "":
            entry.insert(0, placeholder)
            entry.config(fg='#999999')
    
    def validate_coordinates(self, lat, lon):
        try:
            lat_val = float(lat)
            lon_val = float(lon)
            
            if lat_val < self.PANAMA_BOUNDS['min_lat'] or lat_val > self.PANAMA_BOUNDS['max_lat']:
                return False, f"La latitud debe estar entre {self.PANAMA_BOUNDS['min_lat']}° y {self.PANAMA_BOUNDS['max_lat']}° (Panamá)"
            
            if lon_val < self.PANAMA_BOUNDS['min_lon'] or lon_val > self.PANAMA_BOUNDS['max_lon']:
                return False, f"La longitud debe estar entre {self.PANAMA_BOUNDS['min_lon']}° y {self.PANAMA_BOUNDS['max_lon']}° (Panamá)"
            
            return True, None
        except ValueError:
            return False, "Por favor ingrese valores numéricos válidos"
    
    def predict_radiation(self):
        # Obtener valores
        lat = self.lat_entry.get()
        lon = self.lon_entry.get()
        
        # Validar que no sean placeholders
        if lat == "Ej: 8.9824" or lon == "Ej: -79.5199" or lat == "" or lon == "":
            messagebox.showerror("Error", "Por favor ingrese las coordenadas")
            return
        
        # Validar coordenadas
        is_valid, error_msg = self.validate_coordinates(lat, lon)
        if not is_valid:
            messagebox.showerror("Error de Validación", error_msg)
            return
        
        # Simular predicción (aquí conectarías tu modelo de red neuronal)
        # prediction = tu_modelo.predict(lat, lon)
        prediction = round(random.uniform(15, 21), 2)  # Simulación: 15-21 MJ/m²/día
        confidence = round(random.uniform(90, 99), 1)
        
        # Mostrar resultados
        self.show_results(float(lat), float(lon), prediction, confidence)
    
    def show_results(self, lat, lon, prediction, confidence):
        # Limpiar frame de resultados
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        # Mostrar frame
        self.result_frame.pack(fill='both', expand=True, pady=20)
        
        # Título de resultados
        title = tk.Label(
            self.result_frame,
            text="☀ Resultado de la Predicción",
            font=('Arial', 14, 'bold'),
            bg='#fffacd',
            fg='#ff8c00'
        )
        title.pack(pady=10)
        
        # Frame para coordenadas
        coord_frame = tk.Frame(self.result_frame, bg='#ffffff', relief='solid', bd=1)
        coord_frame.pack(fill='x', padx=10, pady=5)
        
        coord_label = tk.Label(
            coord_frame,
            text="📍 Coordenadas:",
            font=('Arial', 10),
            bg='#ffffff',
            fg='#666666'
        )
        coord_label.pack(anchor='w', padx=10, pady=(5, 0))
        
        coord_value = tk.Label(
            coord_frame,
            text=f"{lat:.4f}°, {lon:.4f}°",
            font=('Arial', 12, 'bold'),
            bg='#ffffff',
            fg='#333333'
        )
        coord_value.pack(anchor='w', padx=10, pady=(0, 5))
        
        # Frame para radiación
        rad_frame = tk.Frame(self.result_frame, bg='#ffffff', relief='solid', bd=1)
        rad_frame.pack(fill='x', padx=10, pady=5)
        
        rad_label = tk.Label(
            rad_frame,
            text="☀ Radiación Solar Neta:",
            font=('Arial', 10),
            bg='#ffffff',
            fg='#666666'
        )
        rad_label.pack(anchor='w', padx=10, pady=(5, 0))
        
        rad_value = tk.Label(
            rad_frame,
            text=f"{prediction} MJ/m²/día",
            font=('Arial', 16, 'bold'),
            bg='#ffffff',
            fg='#ff8c00'
        )
        rad_value.pack(anchor='w', padx=10, pady=(0, 5))
        
        # Frame para confianza
        conf_frame = tk.Frame(self.result_frame, bg='#ffffff', relief='solid', bd=1)
        conf_frame.pack(fill='x', padx=10, pady=5)
        
        conf_label = tk.Label(
            conf_frame,
            text="📊 Confianza del Modelo:",
            font=('Arial', 10),
            bg='#ffffff',
            fg='#666666'
        )
        conf_label.pack(anchor='w', padx=10, pady=(5, 0))
        
        conf_value = tk.Label(
            conf_frame,
            text=f"{confidence}%",
            font=('Arial', 14, 'bold'),
            bg='#ffffff',
            fg='#00aa00'
        )
        conf_value.pack(anchor='w', padx=10, pady=(0, 5))
    
    def clear_fields(self):
        self.lat_entry.delete(0, tk.END)
        self.lon_entry.delete(0, tk.END)
        self.lat_entry.insert(0, "Ej: 8.9824")
        self.lon_entry.insert(0, "Ej: -79.5199")
        self.lat_entry.config(fg='#999999')
        self.lon_entry.config(fg='#999999')
        self.result_frame.pack_forget()

# Crear y ejecutar la aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = SolarRadiationPredictor(root)
    root.mainloop()