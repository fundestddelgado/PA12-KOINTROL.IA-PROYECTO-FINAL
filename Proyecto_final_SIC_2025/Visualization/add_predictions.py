import sys
import os
import pandas as pd
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

from Models.predict import predict_from_dataframe

# ============================================
# Cargar dataset
# ============================================
df = pd.read_csv("Datasets/solar_merged_clean.csv")

# ============================================
# Transformaciones geograficas
# ============================================
df["lat_rad"] = np.radians(df["lat"])
df["lon_rad"] = np.radians(df["lon"])

df["sin_lat"] = np.sin(df["lat_rad"])
df["cos_lat"] = np.cos(df["lat_rad"])
df["sin_lon"] = np.sin(df["lon_rad"])
df["cos_lon"] = np.cos(df["lon_rad"])

# ============================================
# Transformaciones temporales
# ============================================
df["date"] = pd.to_datetime(df["date"], errors="coerce")

df["dayofyear"] = df["date"].dt.dayofyear
df["dayofyear_norm"] = df["dayofyear"] / 365.0

df["sin_doy"] = np.sin(2 * np.pi * df["dayofyear"] / 365.0)
df["cos_doy"] = np.cos(2 * np.pi * df["dayofyear"] / 365.0)

# ============================================
# Variables derivadas
# ============================================
df["surface_net_solar_radiation_sum_lag1"] = (
    df["surface_net_solar_radiation_sum"].shift(1)
)

df["temp_humidity_index"] = (
    df["temperature_2m_C"] * (df["relative_humidity"] / 100.0)
)

df["cloud_pressure_ratio"] = (
    df["Cloud_Cover_Mean_24h"] / df["surface_pressure"]
)

# ============================================
# Limpiar NaN
# ============================================
df = df.dropna().reset_index(drop=True)

# ============================================
# Predicciones
# ============================================
df["radiation_pred"] = predict_from_dataframe(df)

# ============================================
# Guardar resultado
# ============================================
df.to_csv("Datasets/solar_with_predictions.csv", index=False)

print("Dataset con predicciones generado correctamente")
print(df[["surface_net_solar_radiation_sum", "radiation_pred"]].head())
print(df[["surface_net_solar_radiation_sum", "radiation_pred"]].describe())