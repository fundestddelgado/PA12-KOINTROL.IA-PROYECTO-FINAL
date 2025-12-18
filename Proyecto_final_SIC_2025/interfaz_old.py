import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import random
from Visualization.corregimientos_map import generate_and_save_map 

class SolarRadiationMapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Proyecto Final IA | Predictor y Mapa de Radiación Solar")
        self.root.geometry("800x750") # Tamaño ajustado para las pestañas
        self.root.configure(bg='#f0f8ff')
        
        self.PANAMA_BOUNDS = {
            'min_lat': 7.0,
            'max_lat': 9.7,
            'min_lon': -83.0,
            'max_lon': -77.0
        }
        
        # Estilo para las pestañas
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('TNotebook.Tab', font=('Arial', 12, 'bold'), padding=[10, 5])
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, padx=10, fill='both', expand=True)

        self.create_header()
        self.create_map_tab()
        self.create_predictor_tab()
        self.create_footer()

    def create_header(self):
        # Header Frame (fuera del Notebook para que sea constante)
        header_frame = tk.Frame(self.root, bg='#0066cc', pady=15)
        header_frame.pack(fill='x', before=self.notebook)
        
        title_label = tk.Label(
            header_frame,
            text="☀ Sistema de Prediccion de Radiación Solar Usando Variables Climaticas",
            font=('Arial', 15, 'bold'),
            bg='#0066cc',
            fg='white'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text="Predicción Local y Visualización por Corregimiento",
            font=('Arial', 11),
            bg='#0066cc',
            fg='white'
        )
        subtitle_label.pack(pady=(0, 5))

    ## --- PESTAÑA 1: PREDICTOR ---
    def create_predictor_tab(self):
        predictor_frame = ttk.Frame(self.notebook, padding="20 20 20 10")
        self.notebook.add(predictor_frame, text="2. Predictor por Coordenadas (Proximamente...)")

        # Instrucciones
        instruc_label = tk.Label(
            predictor_frame,
            text="Ingrese las coordenadas geográficas de un punto en Panamá:",
            font=('Arial', 12, 'bold'),
            fg='#333333'
        )
        instruc_label.pack(pady=(0, 20))
        intro_text = """
        NOTA SOBRE EL PREDICTOR DE COORDENADAS: La funcion de predicción en tiempo real por coordenadas será agregada en una etapa posterior en la Hackathon. 
        Actualmente, los valores de radiación solar en la Pestaña 2 son generados artificialmente para demostrar la funcionalidad de la interfaz y la integración del modelo.
        """
        tk.Label(
            predictor_frame,
            text=intro_text,
            font=("Arial", 11),
            justify=tk.LEFT,
            wraplength=700,
            fg="#333333"
        ).pack(pady=(0, 30))

        # Latitud Frame
        lat_frame = tk.Frame(predictor_frame)
        lat_frame.pack(fill='x', pady=10)
        
        tk.Label(lat_frame, text="📍 Latitud (°):", font=('Arial', 11, 'bold'), fg='#333333').pack(anchor='w')
        self.lat_entry = tk.Entry(lat_frame, font=('Arial', 12), relief='solid', bd=2, width=30)
        self.lat_entry.pack(fill='x', pady=(5, 0))
        self.lat_entry.insert(0, "Ej: 8.9824")
        self.lat_entry.bind('<FocusIn>', lambda e: self.clear_placeholder(self.lat_entry, "Ej: 8.9824"))
        self.lat_entry.bind('<FocusOut>', lambda e: self.restore_placeholder(self.lat_entry, "Ej: 8.9824"))
        tk.Label(lat_frame, text=f"Rango válido: {self.PANAMA_BOUNDS['min_lat']}° a {self.PANAMA_BOUNDS['max_lat']}°", font=('Arial', 8), fg='#666666').pack(anchor='w', pady=(2, 0))
        
        # Longitud Frame
        lon_frame = tk.Frame(predictor_frame)
        lon_frame.pack(fill='x', pady=10)
        
        tk.Label(lon_frame, text="📍 Longitud (°):", font=('Arial', 11, 'bold'), fg='#333333').pack(anchor='w')
        self.lon_entry = tk.Entry(lon_frame, font=('Arial', 12), relief='solid', bd=2, width=30)
        self.lon_entry.pack(fill='x', pady=(5, 0))
        self.lon_entry.insert(0, "Ej: -79.5199")
        self.lon_entry.bind('<FocusIn>', lambda e: self.clear_placeholder(self.lon_entry, "Ej: -79.5199"))
        self.lon_entry.bind('<FocusOut>', lambda e: self.restore_placeholder(self.lon_entry, "Ej: -79.5199"))
        tk.Label(lon_frame, text=f"Rango válido: {self.PANAMA_BOUNDS['min_lon']}° a {self.PANAMA_BOUNDS['max_lon']}°", font=('Arial', 8), fg='#666666').pack(anchor='w', pady=(2, 0))
        
        # Buttons Frame
        button_frame = tk.Frame(predictor_frame)
        button_frame.pack(pady=30)
        
        tk.Button(
            button_frame,
            text="🔮 Predecir Radiación Solar",
            font=('Arial', 12, 'bold'),
            bg='#0066cc',
            fg='white',
            relief='raised',
            bd=3,
            padx=20,
            pady=10,
            command=self.predict_radiation,
            cursor='hand2'
        ).pack(side='left', padx=10)
        
        tk.Button(
            button_frame,
            text="🗑 Limpiar",
            font=('Arial', 12),
            bg='#e0e0e0',
            fg='#333333',
            relief='raised',
            bd=3,
            padx=20,
            pady=10,
            command=self.clear_fields,
            cursor='hand2'
        ).pack(side='left', padx=10)
        
        # Results Frame
        self.result_frame = tk.Frame(predictor_frame, bg='#fffacd', relief='solid', bd=2)
        self.result_frame.pack(fill='both', expand=True, pady=20)
        self.result_frame.pack_forget() # Ocultar inicialmente

    # --- PESTAÑA 2: MAPA ---
    def create_map_tab(self):
        map_tab_frame = ttk.Frame(self.notebook, padding="20 20 20 10")
        self.notebook.add(map_tab_frame, text="1. Mapa por Corregimiento ")

        intro_text = """
        Este mapa interactivo muestra la predicción de Radiación Solar Neta promedio 
        por Corregimiento para todo Panamá.

        ⚠️ NOTA IMPORTANTE: El mapa es complejo y se genera utilizando Plotly. 
        Para garantizar la máxima interactividad (zoom, hover) y evitar problemas 
        de renderizado, se abrirá en su navegador web por defecto.

        La primera carga puede tardar unos segundos mientras se procesan los datos (luego se cachea).
        """
        tk.Label(
            map_tab_frame,
            text=intro_text,
            font=("Arial", 11),
            justify=tk.LEFT,
            wraplength=700,
            fg="#333333"
        ).pack(pady=(0, 30))
        
        self.map_status_label = tk.Label(
            map_tab_frame,
            text="Estado: Pendiente de generar/abrir",
            font=("Arial", 10),
            fg="#666666"
        )
        self.map_status_label.pack(pady=10)
        
        # Botón para abrir el mapa
        tk.Button(
            map_tab_frame,
            text="🗺️ Generar y Abrir Mapa Interactivo",
            command=self.open_map_in_browser,
            font=('Arial', 14, 'bold'),
            bg='#4CAF50',
            fg='white',
            relief='raised',
            bd=5,
            activebackground="#388E3C"
        ).pack(pady=20, ipadx=20, ipady=10)

        # Botón para forzar regeneración (solo si los datos cambian)
        tk.Button(
            map_tab_frame,
            text="🔄 Forzar Regeneración del Mapa (si los datos base cambiaron)",
            command=lambda: self.open_map_in_browser(force=True),
            font=('Arial', 9),
            bg='#ff9800',
            fg='white',
            relief='flat',
            bd=1
        ).pack(pady=(40, 0))

    def open_map_in_browser(self, force=False):
        """Genera/carga el mapa HTML y lo abre en el navegador web."""
        self.map_status_label.config(text="Estado: ⌛ Procesando datos. Esto puede tardar unos segundos...", fg="#ff9800")
        self.root.update() # Forzar actualización de la interfaz
        try:
            # Llama a la función que genera/carga el mapa (utilizando el caché)
            map_path = generate_and_save_map(force_regeneration=force) 
            
            webbrowser.open_new_tab(map_path.absolute().as_uri())
            
            if force:
                status_text = f" Mapa REGENERADO y abierto con éxito."
            else:
                status_text = f" Mapa cargado (usando caché) y abierto con éxito."

            self.map_status_label.config(text=status_text, fg="#006600")

        except Exception as e:
            self.map_status_label.config(
                text=f" Error al generar/abrir el mapa. Consulte la consola para ver los detalles. Error: {e}", 
                fg="red"
            )

    ## --- MÉTODOS COMPARTIDOS ---

    def create_footer(self):
        # Footer Frame (debajo del Notebook)
        footer_frame = tk.Frame(self.root, bg='#f0f8ff', pady=10)
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
            
            if not (self.PANAMA_BOUNDS['min_lat'] <= lat_val <= self.PANAMA_BOUNDS['max_lat']):
                return False, f"La latitud debe estar entre {self.PANAMA_BOUNDS['min_lat']}° y {self.PANAMA_BOUNDS['max_lat']}° (Panamá)"
            
            if not (self.PANAMA_BOUNDS['min_lon'] <= lon_val <= self.PANAMA_BOUNDS['max_lon']):
                return False, f"La longitud debe estar entre {self.PANAMA_BOUNDS['min_lon']}° y {self.PANAMA_BOUNDS['max_lon']}° (Panamá)"
            
            return True, None
        except ValueError:
            return False, "Por favor ingrese valores numéricos válidos"
    
    def predict_radiation(self):
        lat = self.lat_entry.get()
        lon = self.lon_entry.get()
        
        if lat == "Ej: 8.9824" or lon == "Ej: -79.5199" or lat == "" or lon == "":
            messagebox.showerror("Error", "Por favor ingrese las coordenadas")
            return
        
        is_valid, error_msg = self.validate_coordinates(lat, lon)
        if not is_valid:
            messagebox.showerror("Error de Validación", error_msg)
            return
        
        # aqui se conectara el modelo de red neuronal 
        prediction = round(random.uniform(15, 21), 2)
        confidence = round(random.uniform(90, 99), 1)
        
        self.show_results(float(lat), float(lon), prediction, confidence)
    
    def show_results(self, lat, lon, prediction, confidence):
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        self.result_frame.pack(fill='both', expand=True, pady=20)
        self.result_frame.config(bg='#fffacd')
        
        # Título de resultados
        title = tk.Label(self.result_frame, text="☀ Resultado de la Predicción", font=('Arial', 14, 'bold'), bg='#fffacd', fg='#ff8c00')
        title.pack(pady=10)
        
        # Detalles de resultados
        details_frame = tk.Frame(self.result_frame, bg='#fffacd')
        details_frame.pack(padx=20, pady=10)

        data = [
            ("📍 Coordenadas:", f"{lat:.4f}°, {lon:.4f}°", 12, '#333333'),
            ("☀ Radiación Solar Neta:", f"{prediction} MJ/m²/día", 16, '#ff8c00'),
            ("📊 Confianza del Modelo:", f"{confidence}%", 14, '#00aa00')
        ]

        for label_text, value_text, font_size, fg_color in data:
            tk.Label(details_frame, text=label_text, font=('Arial', 10), bg='#fffacd', fg='#666666').pack(anchor='w', pady=(5, 0))
            tk.Label(details_frame, text=value_text, font=('Arial', font_size, 'bold'), bg='#fffacd', fg=fg_color).pack(anchor='w', pady=(0, 10))

    
    def clear_fields(self):
        self.lat_entry.delete(0, tk.END)
        self.lon_entry.delete(0, tk.END)
        self.lat_entry.insert(0, "Ej: 8.9824")
        self.lon_entry.insert(0, "Ej: -79.5199")
        self.result_frame.pack_forget()

if __name__ == "__main__":
    root = tk.Tk()
    app = SolarRadiationMapApp(root)
    root.mainloop()