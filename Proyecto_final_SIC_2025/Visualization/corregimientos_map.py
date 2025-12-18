import pandas as pd
import geopandas as gpd
import json
import plotly.express as px
import numpy as np
from pathlib import Path
import os
import time
from dataclasses import dataclass
from typing import Dict, Optional, Union
from pathlib import Path
import numpy as np
import plotly.express as px
from plotly.subplots import make_subplots

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

    PROJECT_ROOT = Path.cwd()
    OUTPUT_FILE = PROJECT_ROOT / "test_map.html"

    ColorscaleType = Union[str, list]

    @dataclass
    class MapConfig:
        mapbox_style: str = "open-street-map"
        zoom: float = 6
        opacity: float = 0.75
        height: int = 700
        color_scale: Optional[list] = None
        margin: Optional[dict] = None

        def __post_init__(self):
            if self.color_scale is None:
                self.color_scale = [(0.0, "#88FF00"), (0.3, "#FFA500"), (1.0, "#FF0000")]
            if self.margin is None:
                self.margin = dict(r=0, t=0, l=0, b=0)


    class ChoroplethMapBuilder:
        """
        Construye y exporta un choropleth mapbox a HTML (sin servidor).
        La interactividad es client-side vía Plotly updatemenus (HTML estático).
        """

        def __init__(
            self,
            gdf_bound2,
            geojson_data: Dict,
            center_lat: float,
            center_lon: float,
            config: Optional[MapConfig] = None
        ):
            self.gdf = gdf_bound2
            self.geojson = geojson_data
            self.center = {"lat": float(center_lat), "lon": float(center_lon)}
            self.config = config or MapConfig()
            self.fig = None

            self._default_featureidkey = "properties.ID_CORR"
            self._default_locations = "ID_CORR"

        def build_base(
            self,
            color_col: str,
            hover_name: str = "Corregimiento",
            hover_data: Optional[Dict] = None,
            title: Optional[str] = None,
        ):
            if hover_data is None:
                hover_data = {"Provincia": True, color_col: ":.2f"}

            self.fig = px.choropleth_mapbox(
                self.gdf,
                geojson=self.geojson,
                locations=self._default_locations,
                featureidkey=self._default_featureidkey,
                color=color_col,
                mapbox_style=self.config.mapbox_style,
                zoom=self.config.zoom,
                center=self.center,
                opacity=self.config.opacity,
                height=self.config.height,
                color_continuous_scale=self.config.color_scale,
                hover_name=hover_name,
                hover_data=hover_data,
                title=title
            )
            self.fig.update_layout(margin=self.config.margin)
            return self

        def add_variable_selector(
            self,
            variables: Dict[str, str],
            default: Optional[str] = None,
            dropdown_title: str = "Variable",
            x: float = 0.01,
            y: float = 0.99
        ):
            if self.fig is None:
                raise RuntimeError("Primero llama build_base() antes de add_variable_selector().")
            if not variables:
                raise ValueError("variables está vacío.")

            missing = [c for c in variables.keys() if c not in self.gdf.columns]
            if missing:
                raise ValueError(f"Estas columnas no existen en el GeoDataFrame: {missing}")

            if default is None:
                default = next(iter(variables.keys()))
            if default not in variables:
                raise ValueError(f"default='{default}' no está dentro de variables.")

            z0 = np.nan_to_num(self.gdf[default].to_numpy(), nan=0.0)
            self.fig.data[0].z = z0
            self.fig.update_layout(coloraxis_colorbar=dict(title=variables[default]))

            buttons = []
            for col, label in variables.items():
                z = np.nan_to_num(self.gdf[col].to_numpy(), nan=0.0)
                buttons.append(
                    dict(
                        label=label,
                        method="update",
                        args=[
                            {"z": [z]},
                            {"coloraxis": {"colorbar": {"title": {"text": label}}}}
                        ],
                    )
                )

            # Merge con updatemenus existentes si ya había (ej. paletas)
            existing = list(self.fig.layout.updatemenus) if self.fig.layout.updatemenus else []
            existing.append(
                dict(
                    type="dropdown",
                    direction="down",
                    x=x, y=y,
                    xanchor="left", yanchor="top",
                    showactive=True,
                    buttons=buttons,
                    bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="rgba(0,0,0,0.2)",
                    borderwidth=1,
                )
            )

            ann = list(self.fig.layout.annotations) if self.fig.layout.annotations else []
            ann.append(
                dict(
                    text=dropdown_title,
                    x=x, y=y + 0.045,
                    xref="paper", yref="paper",
                    showarrow=False,
                    align="left",
                    font=dict(size=12),
                )
            )

            self.fig.update_layout(updatemenus=existing, annotations=ann)
            return self

        def add_colorscale_selector(
            self,
            scales: Dict[str, ColorscaleType],
            default_key: Optional[str] = None,
            dropdown_title: str = "Paleta",
            x: float = 0.22,
            y: float = 0.99
        ):
            if self.fig is None:
                raise RuntimeError("Primero llama build_base() antes de add_colorscale_selector().")
            if not scales:
                raise ValueError("scales está vacío.")

            if default_key is None:
                default_key = next(iter(scales.keys()))
            if default_key not in scales:
                raise ValueError(f"default_key='{default_key}' no está dentro de scales.")

            self.fig.update_layout(coloraxis=dict(colorscale=scales[default_key]))

            buttons = []
            for key, scale_value in scales.items():
                buttons.append(
                    dict(
                        label=key,
                        method="relayout",
                        args=[{"coloraxis.colorscale": scale_value}],
                    )
                )

            existing = list(self.fig.layout.updatemenus) if self.fig.layout.updatemenus else []
            existing.append(
                dict(
                    type="dropdown",
                    direction="down",
                    x=x, y=y,
                    xanchor="left", yanchor="top",
                    showactive=True,
                    buttons=buttons,
                    bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="rgba(0,0,0,0.2)",
                    borderwidth=1,
                )
            )

            ann = list(self.fig.layout.annotations) if self.fig.layout.annotations else []
            ann.append(
                dict(
                    text=dropdown_title,
                    x=x, y=y + 0.045,
                    xref="paper", yref="paper",
                    showarrow=False,
                    align="left",
                    font=dict(size=12),
                )
            )

            self.fig.update_layout(updatemenus=existing, annotations=ann)
            return self

    # Exporta el cache del mapa en html
        def export_html(self, output_path, include_plotlyjs: str = "cdn", full_html: bool = True):
            if self.fig is None:
                raise RuntimeError("No hay figura. Llama build_base() antes de export_html().")
            self.fig.write_html(str(output_path), include_plotlyjs=include_plotlyjs, full_html=full_html)
            return output_path

    variables = {
        "radiation_pred_filled": "Radiación (pred)",
        "temperature_2m_C_filled": "Temperatura (°C)",
        "relative_humidity_filled": "Humedad relativa (%)",
        "Cloud_Cover_Mean_24h_filled": "Cobertura nubosa (24h)",
        "wind_speed_filled": "Velocidad del viento",
        "surface_pressure_filled": "Presión superficial"
    }

    panel_fields = {
        "Provincia": "Provincia",
        "Distrito": "Distrito",
        "Corregimiento": "Corregimiento",
        "radiation_pred_filled": "Radiación (pred)",
        "temperature_2m_C_filled": "Temperatura (°C)",
        "relative_humidity_filled": "Humedad (%)",
        "Cloud_Cover_Mean_24h_filled": "Nubosidad (24h)",
        "elevation_filled": "Elevación (m)"
    }


    PRESET = [(0.0, "#88FF00"), (0.3, "#FFA500"), (1.0, "#FF0000")]

    palette_options = {
        "Solar Potential Scale": PRESET,
        "Thermal Intensity Scale": "YlOrRd",
        "Perceptual Uniform Scale": "Cividis",
        "Environmental Gradient": "Viridis",
    }


    builder = ChoroplethMapBuilder(
        gdf_bound2=gdf_bound2,
        geojson_data=panama_map_data,
        center_lat=df["lat"].mean(),
        center_lon=df["lon"].mean(),
        config=MapConfig(height=700)
    )

    builder.build_base(
        color_col="radiation_pred_filled",
        hover_name="Corregimiento",
        hover_data={
            "ID_CORR": False,
            "Provincia": True,
            "radiation_pred_filled": ":.2f",
            "Cloud_Cover_Mean_24h_filled": ":.2f",
            "elevation_filled": ":.0f",
            "relative_humidity_filled": ":.2f",
            "temperature_2m_C_filled": ":.2f",
        }
    ).add_variable_selector(
        variables=variables,
        default="radiation_pred_filled",
        dropdown_title="Variable"
    ).add_colorscale_selector(
        scales=palette_options,
        default_key="Solar Potential Scale",
        dropdown_title="Paleta"
    ).export_html(OUTPUT_FILE)