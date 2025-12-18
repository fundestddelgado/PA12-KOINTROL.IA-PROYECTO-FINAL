import pandas as pd
import json

def parse_geo(raw):
    if not isinstance(raw, str):
        return None
    fixed = raw.replace('""', '"').strip()
    if fixed.startswith('"') and fixed.endswith('"'):
        fixed = fixed[1:-1]
    fixed = fixed.replace("false", "False").replace("true", "True")
    return eval(fixed)

def extract(df):
    df["coords"] = df[".geo"].apply(parse_geo)
    df["lon"] = df["coords"].apply(lambda x: x["coordinates"][0] if x else None)
    df["lat"] = df["coords"].apply(lambda x: x["coordinates"][1] if x else None)

    # Nuevo: redondeo a 7 decimales
    df["lon"] = df["lon"].round(7)
    df["lat"] = df["lat"].round(7)

    df["date"] = pd.to_datetime(df["date"])
    return df[["lon","lat","date"]]

dt1 = pd.read_csv(r"C:\Users\alan7\OneDrive\Documentos\Codigo\Python\Proyectos\SolarKointrol\Panama_AgERA5_JanJun2025.csv").head(500)
dt2 = pd.read_csv(r"C:\Users\alan7\OneDrive\Documentos\Codigo\Python\Proyectos\SolarKointrol\Panama_ClimateVars_Clean_JanJun2025.csv").head(500)
dt3 = pd.read_csv(r"C:\Users\alan7\OneDrive\Documentos\Codigo\Python\Proyectos\SolarKointrol\Panama_ERA5Land_JanJun2025.csv").head(500)


d1 = extract(dt1)
d2 = extract(dt2)
d3 = extract(dt3)

print("Unique keys dt1:", len(d1.drop_duplicates()))
print("Unique keys dt2:", len(d2.drop_duplicates()))
print("Unique keys dt3:", len(d3.drop_duplicates()))

print("Intersection dt1 ∩ dt2:", len(pd.merge(d1, d2, on=["lon","lat","date"], how="inner")))
print("Intersection dt1 ∩ dt3:", len(pd.merge(d1, d3, on=["lon","lat","date"], how="inner")))
print("Intersection dt2 ∩ dt3:", len(pd.merge(d2, d3, on=["lon","lat","date"], how="inner")))
