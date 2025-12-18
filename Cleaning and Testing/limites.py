import sys
import os
import numpy as np
import pandas as pd
from datetime import date

# Aseguramos que Python encuentre tus módulos
sys.path.append(os.getcwd())

try:
    from Hackaton_SIC_2025.modulos_gee.modulos_gee import Solicitud, DataFetcher
    print("✅ Módulos importados correctamente.")
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)

# --- CONFIGURACIÓN DEL BARRIDO ---
# Límites aproximados de Panamá (un poco más amplios para probar bordes)
MIN_LAT = 7.0
MAX_LAT = 10.0
MIN_LON = -83.5
MAX_LON = -77.0

# Resolución del paso (grados). 
# 0.2 es aprox cada 22km. Bájalo a 0.1 para más precisión (tardará más).
STEP = 0.2 

def scan_coordinates():
    print(f"Iniciando escaneo de cuadrícula...")
    print(f"Latitud: {MIN_LAT} a {MAX_LAT}")
    print(f"Longitud: {MIN_LON} a {MAX_LON}")
    print(f"Paso: {STEP}°")
    
    lats = np.arange(MIN_LAT, MAX_LAT, STEP)
    lons = np.arange(MIN_LON, MAX_LON, STEP)
    
    valid_points = []
    invalid_points = []
    
    total_points = len(lats) * len(lons)
    count = 0
    
    print(f"Total de puntos a verificar: {total_points}\n")

    for lat in lats:
        for lon in lons:
            count += 1
            # Imprimir progreso cada 10 puntos
            if count % 10 == 0:
                print(f"Procesando punto {count}/{total_points}...", end='\r')

            coords = [float(lon), float(lat)]
            
            try:
                # 1. Preparamos solicitud (usamos elevación como prueba rápida)
                solicitud = Solicitud(coords)
                # Pedimos solo 1 variable para que sea rápido
                detalles = solicitud.hacer_solicitud(['elevacion'], fecha=None)
                
                # 2. Fetch
                fetcher = DataFetcher(detalles, include_meta=False)
                data = fetcher.fetch()
                
                # 3. Validar
                # Si aplicaste mi corrección del buffer, esto debería ser > 0 cerca de la costa
                valor = data.get('elevacion', 0)
                
                if valor != 0:
                    valid_points.append({'lat': lat, 'lon': lon, 'val': valor})
                    # print(f"✅ {lat:.2f}, {lon:.2f} -> {valor}") # Descomentar para ver cada acierto
                else:
                    invalid_points.append({'lat': lat, 'lon': lon})
                    # print(f"❌ {lat:.2f}, {lon:.2f} -> Sin datos") # Descomentar para ver fallos
                    
            except Exception as e:
                print(f"\n⚠️ Error en {lat:.2f}, {lon:.2f}: {e}")

    print("\n\n" + "="*40)
    print(" RESULTADOS DEL ANÁLISIS DE RANGO")
    print("="*40)
    
    if valid_points:
        df = pd.DataFrame(valid_points)
        
        min_valid_lat = df['lat'].min()
        max_valid_lat = df['lat'].max()
        min_valid_lon = df['lon'].min()
        max_valid_lon = df['lon'].max()
        
        print(f"✅ Puntos Válidos encontrados: {len(valid_points)}")
        print(f"❌ Puntos Vacíos (Mar/Fuera): {len(invalid_points)}")
        
        print(f"\n--- RANGO EFECTIVO DE COORDENADAS (Donde GEE responde) ---")
        print(f"Latitud  (Y): {min_valid_lat:.4f}  hasta  {max_valid_lat:.4f}")
        print(f"Longitud (X): {min_valid_lon:.4f}  hasta  {max_valid_lon:.4f}")
        
        print("\nPrueba ingresar estas coordenadas medias en tu interfaz:")
        mid_lat = (min_valid_lat + max_valid_lat) / 2
        mid_lon = (min_valid_lon + max_valid_lon) / 2
        print(f"Lat: {mid_lat:.4f}")
        print(f"Lon: {mid_lon:.4f}")
        
    else:
        print("❌ No se encontraron datos válidos en ningún punto.")
        print("Verifica tu conexión a internet, credenciales o la lógica del Buffer en modulos_gee.py")

if __name__ == "__main__":
    scan_coordinates()