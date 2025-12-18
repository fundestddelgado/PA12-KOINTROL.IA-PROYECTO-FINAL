import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import threading
import json
import os
import sys 
from datetime import date, timedelta
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    # Importaciones de módulos de IA
    from Hackaton_SIC_2025.modulos_gee.feature_generator import feature_generator
    from Proyecto_final_SIC_2025.Models.predict import predict_from_dataframe
    print("✅ Módulos importados correctamente.")
except ImportError as e:
    print(f"Error crítico importando módulos: {e}")
    print(f"Ruta actual: {current_dir}")
    print(f"Raíz del proyecto detectada: {project_root}")
    print(f"Sys.path: {sys.path}")

class SolarRadiationMapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Proyecto Final IA | Predictor y Mapa de Radiación Solar")
       
        self.root.geometry("900x780") 
        self.root.configure(bg='#f0f8ff')
        
        # Cargar datos GeoJSON
        self.locations_data = self.load_geojson_data()
        
        self.PANAMA_BOUNDS = {
            'min_lat': 7.0,
            'max_lat': 9.8,
            'min_lon': -83.5,
            'max_lon': -77.1
        }
        
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('TNotebook.Tab', font=('Arial', 12, 'bold'), padding=[10, 5])
        
        self.create_header()
        
        # Notebook principal
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=5, padx=10, fill='both', expand=True)

        self.create_map_tab()
        self.create_predictor_tab()
        self.create_footer()

    def load_geojson_data(self):
        """Carga el GeoJSON para la funcionalidad de dropdowns."""
        data_structure = {}
        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(base_path, "Panama_Boundaries.geojson")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                geojson = json.load(f)
            
            for feature in geojson['features']:
                props = feature['properties']
                prov = props.get('Provincia', 'Desconocido')
                corr = props.get('Corregimiento', 'Desconocido')
                
                geom = feature['geometry']
                if geom['type'] == 'MultiPolygon':
                    coords = geom['coordinates'][0][0]
                elif geom['type'] == 'Polygon':
                    coords = geom['coordinates'][0]
                else:
                    continue
                
                lons = [p[0] for p in coords]
                lats = [p[1] for p in coords]
                centroid = (sum(lats) / len(lats), sum(lons) / len(lons))
                
                if prov not in data_structure:
                    data_structure[prov] = {}
                data_structure[prov][corr] = centroid
                
            return {k: dict(sorted(v.items())) for k, v in sorted(data_structure.items())}
        except Exception as e:
            print(f"Error cargando GeoJSON: {e}")
            return {}

    def create_header(self):
        header_frame = tk.Frame(self.root, bg='#0066cc', pady=10)
        header_frame.pack(fill='x', side='top')
        
        title_label = tk.Label(
            header_frame,
            text="☀ Sistema de Prediccion de Radiación Solar Usando Variables Climaticas",
            font=('Arial', 14, 'bold'), # Fuente ligeramente ajustada
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
        subtitle_label.pack(pady=(0, 2))

    # --- PESTAÑA 2: ---
    def create_predictor_tab(self):
        predictor_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(predictor_frame, text="2. Predictor por Coordenadas")

        instruc_label = tk.Label(
            predictor_frame,
            text="Ingrese las coordenadas geográficas de un punto en Panamá:",
            font=('Arial', 12, 'bold'),
            fg='#333333'
        )
        instruc_label.pack(pady=(0, 5))
        
        intro_text = """
        Este módulo conecta con Google Earth Engine para extraer variables climáticas (Humedad, Viento, etc.)
        y utiliza una Red Neuronal para predecir la radiación solar incidente.
        Seleccione un corregimiento o ingrese coordenadas manuales.
        """
        tk.Label(
            predictor_frame,
            text=intro_text,
            font=("Arial", 10),
            justify=tk.LEFT,
            fg="#555555"
        ).pack(pady=(0, 10))

        # --- CONTENEDOR INPUTS ---
        inputs_container = tk.Frame(predictor_frame)
        inputs_container.pack(fill='x', padx=10)

        # 1. Selección (Izquierda)
        loc_frame = tk.LabelFrame(inputs_container, text="📍 Selección Rápida", font=('Arial', 10, 'bold'), padx=10, pady=5)
        loc_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        tk.Label(loc_frame, text="Provincia:", font=('Arial', 9)).pack(anchor='w')
        self.prov_combo = ttk.Combobox(loc_frame, state="readonly")
        self.prov_combo.pack(fill='x', pady=(0, 5))
        self.prov_combo['values'] = list(self.locations_data.keys())
        self.prov_combo.bind("<<ComboboxSelected>>", self.on_prov_selected)

        tk.Label(loc_frame, text="Corregimiento:", font=('Arial', 9)).pack(anchor='w')
        self.corr_combo = ttk.Combobox(loc_frame, state="readonly")
        self.corr_combo.pack(fill='x')
        self.corr_combo.bind("<<ComboboxSelected>>", self.on_corr_selected)

        # 2. Coordenadas (Derecha)
        coord_frame = tk.LabelFrame(inputs_container, text="🌐 Coordenadas", font=('Arial', 10, 'bold'), padx=10, pady=5)
        coord_frame.pack(side='left', fill='both', expand=True, padx=(5, 0))

        tk.Label(coord_frame, text="Latitud (°):", font=('Arial', 9)).pack(anchor='w')
        self.lat_entry = tk.Entry(coord_frame, font=('Arial', 11), relief='solid', bd=1)
        self.lat_entry.pack(fill='x', pady=(0, 5))
        self.lat_entry.insert(0, "8.9824")

        tk.Label(coord_frame, text="Longitud (°):", font=('Arial', 9)).pack(anchor='w')
        self.lon_entry = tk.Entry(coord_frame, font=('Arial', 11), relief='solid', bd=1)
        self.lon_entry.pack(fill='x')
        self.lon_entry.insert(0, "-79.5199")

        # --- BOTONES ---
        button_frame = tk.Frame(predictor_frame)
        button_frame.pack(pady=15)
        
        self.btn_predict = tk.Button(
            button_frame,
            text="🔮 Predecir Radiación Solar",
            font=('Arial', 11, 'bold'),
            bg='#0066cc', fg='white', relief='raised', bd=3,
            padx=15, pady=5,
            command=self.start_prediction_thread, cursor='hand2'
        )
        self.btn_predict.pack(side='left', padx=10)
        
        tk.Button(
            button_frame,
            text="🗑 Limpiar",
            font=('Arial', 11),
            bg='#e0e0e0', fg='#333333', relief='raised', bd=3,
            padx=15, pady=5,
            command=self.clear_fields, cursor='hand2'
        ).pack(side='left', padx=10)

        self.loading_label = tk.Label(predictor_frame, text="", font=('Arial', 10, 'italic'), fg='#0066cc')
        self.loading_label.pack()
        
        # --- FRAME DE RESULTADOS (Espacio reservado) ---
        self.result_frame = tk.Frame(predictor_frame, bg='#fffacd', relief='solid', bd=1)
        # fill='both' y expand=True aseguran que ocupe el resto del espacio disponible
        self.result_frame.pack(fill='both', expand=True, pady=(5, 10))
        self.result_frame.pack_forget()

    # --- LÓGICA DE INTERFAZ ---
    def on_prov_selected(self, event):
        selected_prov = self.prov_combo.get()
        if selected_prov in self.locations_data:
            self.corr_combo['values'] = list(self.locations_data[selected_prov].keys())
            self.corr_combo.set('')

    def on_corr_selected(self, event):
        prov = self.prov_combo.get()
        corr = self.corr_combo.get()
        if prov in self.locations_data and corr in self.locations_data[prov]:
            lat, lon = self.locations_data[prov][corr]
            self.lat_entry.delete(0, tk.END)
            self.lat_entry.insert(0, f"{lat:.4f}")
            self.lon_entry.delete(0, tk.END)
            self.lon_entry.insert(0, f"{lon:.4f}")

    # --- LÓGICA DE PREDICCIÓN ---
    def start_prediction_thread(self):
        lat = self.lat_entry.get()
        lon = self.lon_entry.get()
        
        if not lat or not lon:
            messagebox.showerror("Error", "Ingrese coordenadas válidas.")
            return

        try:
            lat_val, lon_val = float(lat), float(lon)
            if not (self.PANAMA_BOUNDS['min_lat'] <= lat_val <= self.PANAMA_BOUNDS['max_lat'] and 
                    self.PANAMA_BOUNDS['min_lon'] <= lon_val <= self.PANAMA_BOUNDS['max_lon']):
                messagebox.showerror("Error", "Coordenadas fuera de Panamá.")
                return
        except ValueError:
            messagebox.showerror("Error", "Valores numéricos inválidos.")
            return

        self.btn_predict.config(state='disabled', bg='#cccccc')
        self.loading_label.config(text="⌛ Conectando con satélite y procesando modelo...")
        self.result_frame.pack_forget()

        threading.Thread(target=self.run_prediction_logic, args=(lat_val, lon_val)).start()

    def run_prediction_logic(self, lat, lon):
        try:
            target_date = date.today() - timedelta(days=20)
            date_str = target_date.strftime("%Y-%m-%d")

            df_features, real_value = feature_generator([lon, lat], target_date=date_str)
            
            pred_joules = float(predict_from_dataframe(df_features)[0])
            
            # Conversión a MJ
            pred_mj = pred_joules / 1_000_000
            real_mj = (real_value / 1_000_000) if real_value > 0 else 0.0

            if real_value > 0:
                diff = abs(pred_joules - real_value)
                conf = max(0, 100 - (diff / real_value * 100))
            else:
                conf = 0.0

            self.root.after(0, lambda: self.show_results(lat, lon, pred_mj, conf, real_mj))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, lambda: [self.btn_predict.config(state='normal', bg='#0066cc'), self.loading_label.config(text="")])

    def show_results(self, lat, lon, pred_mj, conf, real_mj):
        for w in self.result_frame.winfo_children(): w.destroy()
        
        self.result_frame.pack(fill='both', expand=True, pady=10)
        self.result_frame.config(bg='#fffacd')
        
        # Título
        tk.Label(self.result_frame, text="☀ Resultado de la Predicción", font=('Arial', 13, 'bold'), bg='#fffacd', fg='#ff8c00').pack(pady=(10, 5))
        
        # --- GRID LAYOUT PARA AHORRAR ESPACIO ---
        # Usamos Grid para poner Predicción y Real lado a lado
        grid_frame = tk.Frame(self.result_frame, bg='#fffacd')
        grid_frame.pack(fill='x', padx=20, pady=5)
        
        # Columna 0: Predicción (Izquierda)
        tk.Label(grid_frame, text="☀ Radiación Solar (IA):", font=('Arial', 10), bg='#fffacd', fg='#666').grid(row=0, column=0, sticky='w', pady=(0,2))
        tk.Label(grid_frame, text=f"{pred_mj:.2f} MJ/m²/día", font=('Arial', 16, 'bold'), bg='#fffacd', fg='#ff8c00').grid(row=1, column=0, sticky='w', pady=(0,10))

        # Separador visual (Columna 1)
        tk.Frame(grid_frame, width=20, bg='#fffacd').grid(row=0, column=1)

        # Columna 2: Dato Real (Derecha)
        if real_mj > 0:
            real_text = f"{real_mj:.2f} MJ/m²/día"
            diff = pred_mj - real_mj
            status = "Sobre" if diff > 0 else "Sub"
            comp_txt = f"Dif: {abs(diff):.2f} MJ ({status})"
            comp_col = '#555555'
        else:
            real_text = "N/A (Mar/Nubes)"
            comp_txt = "Sin Comparación"
            comp_col = '#999999'

        tk.Label(grid_frame, text="🛰️ Dato Real (Validación):", font=('Arial', 10), bg='#fffacd', fg='#666').grid(row=0, column=2, sticky='w', pady=(0,2))
        tk.Label(grid_frame, text=real_text, font=('Arial', 16, 'bold'), bg='#fffacd', fg='#333').grid(row=1, column=2, sticky='w', pady=(0,10))

        # Fila 2: Detalles técnicos 
        info_frame = tk.Frame(self.result_frame, bg='#fffacd', highlightbackground="#eeeeee", highlightthickness=1)
        info_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        # Función auxiliar para filas compactas
        def add_row(parent, label, value, color, r):
            tk.Label(parent, text=label, font=('Arial', 10), bg='#fffacd', fg='#666').grid(row=r, column=0, sticky='w', padx=5, pady=2)
            tk.Label(parent, text=value, font=('Arial', 10, 'bold'), bg='#fffacd', fg=color).grid(row=r, column=1, sticky='w', padx=5, pady=2)

        add_row(info_frame, "📍 Ubicación:", f"{lat:.4f}°, {lon:.4f}°", '#333', 0)
        add_row(info_frame, "⚖️ Comparación:", comp_txt, comp_col, 1)
        add_row(info_frame, "📊 Confianza Modelo:", f"{conf:.1f}%", '#00aa00', 2)

    # --- PESTAÑA 1: MAPA WEB ---
    def create_map_tab(self):
        map_tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(map_tab, text="1. Mapa por Corregimiento ")

        intro_text = """
        Este mapa interactivo muestra la predicción de Radiación Solar Neta promedio 
        por Corregimiento para todo Panamá.

        ⚠️ NOTA IMPORTANTE: El mapa es complejo y se genera utilizando Plotly. 
        Para garantizar la máxima interactividad (zoom, hover) y evitar problemas 
        de renderizado, se abrirá en su navegador web por defecto.
        """
        tk.Label(
            map_tab, text=intro_text, font=("Arial", 11), 
            justify=tk.LEFT, bg='#f0f8ff'
        ).pack(pady=(0, 30))
        
        tk.Button(
            map_tab, 
            text="🗺️ Generar y Abrir Mapa Interactivo", 
            command=lambda: webbrowser.open("https://app-demo-pvwbr6radvuqjubaaphkgu.streamlit.app/"),
            font=('Arial', 14, 'bold'), bg='#4CAF50', fg='white', 
            relief='raised', bd=4, padx=20, pady=10, cursor='hand2'
        ).pack(pady=20)

    def create_footer(self):
        footer = tk.Frame(self.root, bg='#f0f8ff', pady=5)
        footer.pack(fill='x', side='bottom')
        
        tk.Label(footer, text="Equipo: Alan Sánchez, Abdiel Bernal, Ernesto Jurado, Ana Flores", font=('Arial', 9), bg='#f0f8ff', fg='#333').pack()
        tk.Label(footer, text="Proyecto Final - Módulo Inteligencia Artificial - Hackathon | SIC 2025", font=('Arial', 8), bg='#f0f8ff', fg='#666').pack()

    def clear_fields(self):
        self.lat_entry.delete(0, tk.END)
        self.lon_entry.delete(0, tk.END)
        self.prov_combo.set('')
        self.corr_combo.set('')
        self.result_frame.pack_forget()

if __name__ == "__main__":
    root = tk.Tk()
    app = SolarRadiationMapApp(root)
    root.mainloop()