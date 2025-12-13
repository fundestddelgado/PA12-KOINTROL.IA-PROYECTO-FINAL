import pandas as pd

path = r"C:\Users\alan7\OneDrive\Documentos\Codigo\Python\Proyectos\solar_merged.csv"

df = pd.read_csv(path)

cols_to_drop = [
    "Temperature_Air_2m_Mean_24h",
    "Temperature_Air_2m_Mean_24h_C",
    "temperature_2m",
    "Wind_Speed_10m_Mean_24h",
    ".geo"
]

# si quieres usar solo temperature_2m_C, elimina esta otra:
# cols_to_drop.append("temperature_2m_C")

df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

# Guardar dataset limpio
df.to_csv("solar_merged_clean.csv", index=False)

print("Dataset limpio guardado como solar_merged_clean.csv")
print("Columnas finales:", df.columns.tolist())
