import os
import numpy as np
import joblib
from keras.models import load_model

BASE_DIR = os.path.dirname(__file__)

model = load_model(os.path.join(BASE_DIR, "solar_model.keras"))
scaler = joblib.load(os.path.join(BASE_DIR, "solar_scaler.pkl"))

target_norm = joblib.load(os.path.join(BASE_DIR, "target_norm.pkl"))
y_mean = target_norm["y_mean"]
y_std = target_norm["y_std"]

FEATURE_COLS = [
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

def predict_from_dataframe(df):
    X = df[FEATURE_COLS].values
    X_scaled = scaler.transform(X)

    y_pred_norm = model.predict(X_scaled, verbose=0).flatten()

    # desnormalizar target
    y_pred = y_pred_norm * y_std + y_mean

    return y_pred
