import ee
import pandas as pd
from datetime import date, timedelta
import math
import os

# --- Manejo Dinámico de Rutas ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
service_account = 'kointrol-team@kointrol-ai.iam.gserviceaccount.com'
key_file = os.path.join(BASE_DIR, "kointrol-ai-218d7c03278d.json")

credentials = ee.ServiceAccountCredentials(service_account, key_file)
ee.Initialize(credentials)

class Solicitud:
    def __init__(self, coords):
        self.coords = coords
        self.registro_variables = {
            'radiacion solar': {
                'dataset': 'ECMWF/ERA5_LAND/DAILY_AGGR',
                'bands': ['surface_net_solar_radiation_sum'],
                'type': 'daily'
            },
            'temperatura': {
                'dataset': 'ECMWF/ERA5_LAND/DAILY_AGGR',
                'bands': ['temperature_2m'],
                'type': 'daily'
            },
            'presion': {
                'dataset': 'ECMWF/ERA5_LAND/DAILY_AGGR',
                'bands': ['surface_pressure'],
                'type': 'daily'
            },
            'precipitacion': {
                'dataset': 'ECMWF/ERA5_LAND/DAILY_AGGR',
                'bands': ['total_precipitation_sum'],
                'type': 'daily'
            },
            'direccion viento': {
                'dataset': 'ECMWF/ERA5_LAND/DAILY_AGGR',
                'bands': ['u_component_of_wind_10m','v_component_of_wind_10m'],
                'type': 'daily'
            },
            'velocidad viento': {
                'dataset': 'ECMWF/ERA5_LAND/DAILY_AGGR',
                'bands': ['u_component_of_wind_10m','v_component_of_wind_10m'],
                'type': 'daily'
            },
            'humedad relativa': {
                'dataset': 'ECMWF/ERA5_LAND/DAILY_AGGR',
                'bands': ['temperature_2m','dewpoint_temperature_2m'],
                'type': 'daily'
            },
            'nubosidad': {
                'dataset': 'ECMWF/ERA5/HOURLY',
                'bands': ['fraction_of_cloud_cover_850hPa'],
                'type': 'hourly'
            },
            'aerosoles': {
                'dataset': 'ECMWF/CAMS/NRT',
                'bands': ['total_aerosol_optical_depth_at_550nm_surface'],
                'type': 'hourly'
            },
            'elevacion': {
                'dataset': 'USGS/SRTMGL1_003',
                'bands': ['elevation'],
                'type': 'static'
            }
        }

    def hacer_solicitud(self, variables, fecha = None):
        if fecha is None:
            # Usamos 20 días atrás para asegurar disponibilidad de datos
            fecha = date.today() - timedelta(days=20)
        elif isinstance(fecha,str):
            fecha = date.fromisoformat(fecha)
            
        selected = {var: self.registro_variables[var]
                    for var in variables if var in self.registro_variables}
        detalles_solicitud = {
            'punto': ee.Geometry.Point(self.coords),
            'fecha_inicio': ee.Date(fecha.isoformat()),
            'fecha_final': ee.Date(fecha.isoformat()).advance(1, 'day'),
            'variables': selected
        }
        return detalles_solicitud


class DataFetcher:
    def __init__(self, solicitud, include_meta=True):
        self.solicitud = solicitud
        self.include_meta = include_meta

    def fetch(self):
        punto = self.solicitud['punto']
        f1 = self.solicitud['fecha_inicio']
        f2 = self.solicitud['fecha_final']

        results = {}
        for var_name, meta in self.solicitud['variables'].items():
            dataset = meta['dataset']
            bands = meta['bands']
            vtype = meta['type']

            if vtype == 'daily' or vtype == 'hourly':
                raw_data = self.get_reduced_value(dataset, bands, f1, f2, punto)
            elif vtype == 'static':
                raw_data = self.get_static_reduced(dataset, bands, punto)
            else:
                raw_data = 0.0

            results[var_name] = self.process_variable_logic(var_name, bands, raw_data)
            
        return results

    def get_reduced_value(self, dataset, bands, f1, f2, punto):
        coll = ee.ImageCollection(dataset).filterDate(f1, f2).select(bands)
        
        if coll.size().getInfo() == 0:
            return {b: 0.0 for b in bands}
            
        img = coll.mean()
        
        # --- SOLUCIÓN CRÍTICA: BUFFER ---
        # Creamos un radio de búsqueda de 5km (5000m) alrededor del punto.
        # Esto permite capturar datos de tierra incluso si el click fue en el mar cercano.
        geometry_buffer = punto.buffer(25000)

        stats = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry_buffer, # Usamos el área circular, no el punto
            scale=10000 
        ).getInfo()
        
        return stats if stats else {b: 0.0 for b in bands}

    def get_static_reduced(self, dataset, bands, punto):
        img = ee.Image(dataset).select(bands)
        stats = img.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=punto.buffer(100), # Pequeño buffer para elevación también
            scale=30
        ).getInfo()
        return stats if stats else {bands[0]: 0.0}

    def process_variable_logic(self, var_name, bands, muestra):
        if not muestra: return 0.0

        if var_name == 'velocidad viento':
            u = muestra.get(bands[0])
            v = muestra.get(bands[1])
            if u is None or v is None: return 0.0
            return (u**2 + v**2)**0.5
        
        elif var_name == 'direccion viento':
            u = muestra.get(bands[0])
            v = muestra.get(bands[1])
            if u is None or v is None: return 0.0
            return (180 / math.pi) * math.atan2(v, u)
            
        elif var_name == 'humedad relativa':
            T = muestra.get(bands[0])
            Td = muestra.get(bands[1])
            if T is not None and Td is not None:
                return 100 * (math.exp((17.625*Td)/(243.04+Td)) / math.exp((17.625*T)/(243.04+T)))
            return 0.0
            
        elif var_name == 'temperatura':
            kelvin = muestra.get(bands[0])
            return kelvin - 273.15 if kelvin is not None else 0.0
            
        else:
            val = muestra.get(bands[0])
            return val if val is not None else 0.0

    def to_dataframe(self):
        results = self.fetch()
        if self.include_meta:
            punto = self.solicitud['punto']
            f1 = self.solicitud['fecha_inicio']
            lon, lat = punto['coordinates']
            results['fecha'] = f1.format('YYYY-MM-dd').getInfo()
            results['lat'] = lat
            results['lon'] = lon
        return pd.DataFrame([results])