import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split

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

df = df.dropna().reset_index(drop=True)

# ============================================
# Features y target
# ============================================
feature_cols = [
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

X = df[feature_cols]
y = df["surface_net_solar_radiation_sum"].values

# ============================================
# MISMO split que entrenamiento
# ============================================
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.20, random_state=42
)

# ============================================
# Recalcular normalizacion del target
# ============================================
y_mean = y_train.mean()
y_std = y_train.std()

print("y_mean:", y_mean)
print("y_std :", y_std)

# ============================================
# Guardar valores
# ============================================
joblib.dump(
    {
        "y_mean": y_mean,
        "y_std": y_std
    },
    "Models/target_norm.pkl"
)

print("target_norm.pkl guardado correctamente")
