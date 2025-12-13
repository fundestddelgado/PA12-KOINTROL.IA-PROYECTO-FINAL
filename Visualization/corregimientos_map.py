import pandas as pd
import geopandas as gpd
import json
import plotly.express as px
import numpy as np
from pathlib import Path
import os
import time

def generate_and_save_map(force_regeneration=False):
    """
    Genera el mapa interactivo de Plotly y lo guarda como un archivo HTML.
    Utiliza un mecanismo de caché para evitar regenerar el archivo si ya existe.
    """
    
    # 1. ESTABLECER RUTAS
    PROJECT_ROOT = Path(__file__).resolve().parent.parent 
    DATA_PATH = PROJECT_ROOT / "Datasets"
    OUTPUT_FILE = PROJECT_ROOT / "solar_radiation_map_cache.html"
    
    # 2. VERIFICAR CACHE
    if OUTPUT_FILE.exists() and not force_regeneration:
        print(f"DEBUG: Mapa cargado desde caché: {OUTPUT_FILE.name}")
        return OUTPUT_FILE
        
    start_time = time.time()
    
    try:
        csv_path = str(DATA_PATH / "solar_with_predictions.csv")
        geojson_path = str(DATA_PATH / "Panama_Boundaries.geojson")
        
        # Lectura de archivos 
        df = pd.read_csv(csv_path)
        panama_map_data = json.load(open(geojson_path, encoding="utf-8"))
        gdf_bound = gpd.read_file(geojson_path, encoding="utf-8") 

    except FileNotFoundError as e:
        print(f"ERROR FATAL: Archivo no encontrado. Asegúrate de que la ruta sea correcta. Error: {e}")
        raise FileNotFoundError(f"Asegúrate de que la carpeta 'Datasets' exista y contenga los archivos requeridos. Ruta base: {DATA_PATH.absolute()}")

    # --- PROCESAMIENTO DE DATOS ---
    vars_mean = [
        'Cloud_Cover_Mean_24h', 'elevation', 'relative_humidity',
        'surface_net_solar_radiation_sum', 'surface_pressure',
        'temperature_2m_C', 'total_precipitation_sum',
        'wind_direction', 'wind_speed', "radiation_pred"
    ]
    
    gdf_points = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['lon'], df['lat']), crs="EPSG:4326")
    joined = gpd.sjoin(gdf_points, gdf_bound, how="left", predicate="within")

    base = gdf_bound[["ID_CORR", "Provincia", 'Corregimiento']].copy()
    base["ID_CORR"] = base["ID_CORR"].astype(str)
    joined["ID_CORR"] = joined["ID_CORR"].astype(str)

    corr_stats = (
        joined.groupby("ID_CORR")
        .agg({c: "mean" for c in vars_mean})
        .reset_index()
    )

    full = base.merge(corr_stats, on="ID_CORR", how="left")

    prov_means = (
        full.groupby("Provincia")[vars_mean]
        .mean()
        .add_prefix("prov_")
        .reset_index()
    )

    full = full.merge(prov_means, on="Provincia", how="left")

    for c in vars_mean:
        global_mean = full[c].mean()
        if np.isnan(global_mean):
             global_mean = 0 
        
        full[c + "_filled"] = full[c].fillna(full["prov_" + c]).fillna(global_mean)

    filled_cols = [c + "_filled" for c in vars_mean]
    to_merge = ["ID_CORR", "Provincia", "Corregimiento"] + filled_cols

    gdf_bound["ID_CORR"] = gdf_bound["ID_CORR"].astype(str)
    gdf_bound2 = gdf_bound.merge(full[to_merge], on="ID_CORR", how="left", suffixes=("", "_dup"))

    for col in ["Provincia", "Corregimiento"]:
        dup = col + "_dup"
        if dup in gdf_bound2.columns:
            gdf_bound2[col] = gdf_bound2[col].fillna(gdf_bound2[dup])
            gdf_bound2.drop(columns=[dup], inplace=True)
            
    # --- PLOTTING ---
    for ft in panama_map_data.get("features", []):
        props = ft.get("properties", {})
        if "ID_CORR" in props and props["ID_CORR"] is not None:
            props["ID_CORR"] = str(props["ID_CORR"])

    fig = px.choropleth_mapbox(
        gdf_bound2,
        geojson=panama_map_data,
        locations="ID_CORR",
        featureidkey="properties.ID_CORR",
        color="radiation_pred_filled",
        mapbox_style="open-street-map",
        zoom=6,
        center={"lat": df["lat"].mean(), "lon": df["lon"].mean()},
        opacity=0.75,
        height=700,
        color_continuous_scale=[(0.0, "#88FF00"), (0.3, "#FFA500"), (1.0, "#FF0000")],
        hover_name="Corregimiento",
        hover_data={
            "ID_CORR": False, "Provincia": True, "radiation_pred_filled": ":.2f",
            "Cloud_Cover_Mean_24h_filled": ":.2f",
            "elevation_filled": ":.0f",
            "relative_humidity_filled": ":.2f",
            "temperature_2m_C_filled": ":.2f",
        } 
    )
    fig.update_layout(margin=dict(r=0, t=0, l=0, b=0)) 
    
    # 3. GUARDA LA FIGURA Y RETORNA LA RUTA
    fig.write_html(str(OUTPUT_FILE), include_plotlyjs='cdn', full_html=True)
    end_time = time.time()
    print(f"DEBUG: Mapa generado y guardado en {round(end_time - start_time, 2)} segundos.")
    return OUTPUT_FILE