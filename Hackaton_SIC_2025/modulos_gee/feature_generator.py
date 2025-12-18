import pandas as pd
import numpy as np
import warnings
# Silenciar avisos de downcasting y nombres de features
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.set_option('future.no_silent_downcasting', True)
from datetime import date, timedelta, datetime
# Importación absoluta basada en la raíz del proyecto
from Hackaton_SIC_2025.modulos_gee.modulos_gee import Solicitud, DataFetcher

def feature_generator(coords, target_date=None):
    """
    Genera el DataFrame con todas las features ingenieriles necesarias para el modelo.
    """
    
    # 1. Definir fechas
    if target_date is None:
        # Por defecto usamos una fecha con datos seguros (hace 20 días para asegurar ERA5)
        date_obj = date.today() - timedelta(days=20)
    else:
        date_obj = date.fromisoformat(target_date)
        
    prev_date_obj = date_obj - timedelta(days=1)
    
    # Variables a pedir a GEE
    vars_list = [
        'nubosidad', 'elevacion', 'humedad relativa', 'radiacion solar',
        'presion', 'temperatura', 'precipitacion', 'direccion viento', 'velocidad viento'
    ]

    # 2. Obtener datos del día objetivo (Target) y día previo (para Lag1)
    # Solicitud Día Objetivo
    solicitud_target = Solicitud(coords)
    detalles_target = solicitud_target.hacer_solicitud(vars_list, fecha=date_obj)
    fetcher_target = DataFetcher(detalles_target)
    df_target = fetcher_target.to_dataframe()

    # Solicitud Día Previo
    solicitud_prev = Solicitud(coords)
    detalles_prev = solicitud_prev.hacer_solicitud(['radiacion solar'], fecha=prev_date_obj)
    fetcher_prev = DataFetcher(detalles_prev)
    df_prev = fetcher_prev.to_dataframe()
    
    # 3. Mapeo de columnas base
    column_map = {
        'nubosidad': 'Cloud_Cover_Mean_24h',
        'elevacion': 'elevation',
        'humedad relativa': 'relative_humidity',
        'radiacion solar': 'surface_net_solar_radiation_sum',
        'presion': 'surface_pressure',
        'temperatura': 'temperature_2m_C',
        'precipitacion': 'total_precipitation_sum'
    }
    
    df_target = df_target.rename(columns=column_map)
    
    # Extraer valor real para validación (si existe)
    real_value = df_target['surface_net_solar_radiation_sum'].iloc[0] if 'surface_net_solar_radiation_sum' in df_target.columns else 0
    
    # Extraer el Lag1 del dataframe previo
    lag1_val = df_prev['radiacion solar'].iloc[0] if 'radiacion solar' in df_prev.columns else 0
    df_target['surface_net_solar_radiation_sum_lag1'] = lag1_val

    # 4. INGENIERÍA DE CARACTERÍSTICAS
    
    # A. Transformaciones Geográficas
    df_target["lat_rad"] = np.radians(df_target["lat"])
    df_target["lon_rad"] = np.radians(df_target["lon"])
    df_target["sin_lat"] = np.sin(df_target["lat_rad"])
    df_target["cos_lat"] = np.cos(df_target["lat_rad"])
    df_target["sin_lon"] = np.sin(df_target["lon_rad"])
    df_target["cos_lon"] = np.cos(df_target["lon_rad"])

    # B. Transformaciones Temporales
    dt = pd.to_datetime(df_target['fecha'])
    dayofyear = dt.dt.dayofyear
    df_target["dayofyear_norm"] = dayofyear / 365.0
    df_target["sin_doy"] = np.sin(2 * np.pi * dayofyear / 365.0)
    df_target["cos_doy"] = np.cos(2 * np.pi * dayofyear / 365.0)

    # C. Variables Derivadas (AQUÍ ESTABA EL ERROR)
    df_target["temp_humidity_index"] = (
        df_target["temperature_2m_C"] * (df_target["relative_humidity"] / 100.0)
    )
    
    pressure_safe = df_target["surface_pressure"].replace(0, 1.0)
    df_target["cloud_pressure_ratio"] = (
        df_target["Cloud_Cover_Mean_24h"] / pressure_safe
    )

    # 5. Seleccionar y ordenar columnas finales
    final_cols = [
        "Cloud_Cover_Mean_24h",
        "relative_humidity",
        "temperature_2m_C",
        "total_precipitation_sum",
        "surface_pressure",
        "elevation",
        "sin_lat",
        "cos_lat",
        "sin_lon",
        "cos_lon",
        "sin_doy",
        "cos_doy",
        "dayofyear_norm",
        "surface_net_solar_radiation_sum_lag1",
        "temp_humidity_index",
        "cloud_pressure_ratio"
    ]
    
    df_final = df_target[final_cols].copy()
    
    # Reemplazar infinitos por 0 
    df_final.replace([np.inf, -np.inf], 0, inplace=True)
    # Reemplazar nulos por 0
    df_final.fillna(0, inplace=True)
    
    return df_final, real_value