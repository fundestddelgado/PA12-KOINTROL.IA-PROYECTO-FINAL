import ee
import pandas as pd
from datetime import date, timedelta
import math

# ---Inicializamos la sesión de Earth Engine con el proyecto especificado---
service_account = 'kointrol-team@kointrol-ai.iam.gserviceaccount.com'
key_file = "kointrol-ai-218d7c03278d.json"

credentials = ee.ServiceAccountCredentials(service_account, key_file)
ee.Initialize(credentials)

# -------------------------Detalles de Solicitud-----------------------------
'''
Observación: se hace la solicitud de la data de hace 8 días para
asegurar la existencia de información a partir de la cual predecir
'''

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

    def hacer_solicitud(self, variables):
        fecha = date.today() - timedelta(days=7)
        selected = {var: self.registro_variables[var]
                    for var in variables if var in self.registro_variables}
        detalles_solicitud = {
            'punto': ee.Geometry.Point(self.coords),
            'fecha_inicio': ee.Date(fecha.isoformat()),
            'fecha_final': ee.Date(fecha.isoformat()).advance(1, 'day'),
            'variables': selected
        }
        return detalles_solicitud

# ---------------------------Extracción de Datos-----------------------------
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
            bands   = meta['bands']
            vtype   = meta['type']

            if vtype == 'daily':
                results[var_name] = self.get_values(var_name, dataset, bands, f1, f2, punto)
            elif vtype == 'hourly':
                results[var_name] = self.get_daily(dataset, bands, f1, f2, punto)
            elif vtype == 'static':
                results[var_name] = self.get_static(dataset, bands, punto)
            else:
                results[var_name] = None
        return results

    def get_static(self, dataset, bands, punto):
        img = ee.Image(dataset).select(bands)
        muestra = img.sample(region=punto, scale=30).first().toDictionary().getInfo()
        return muestra.get(bands[0])

    def get_daily(self, dataset, bands, f1, f2, punto):
        coll = ee.ImageCollection(dataset).filterDate(f1, f2).select(bands)
        count = coll.size().getInfo()
        if count == 0:
            return None
        daily_img = coll.mean()
        muestra = daily_img.sample(region=punto, scale=10000).first().toDictionary().getInfo()
        return muestra.get(bands[0]) if len(bands) == 1 else {b: muestra.get(b) for b in bands}

    def get_sample(self, dataset, bands, f1, f2, punto):
        coll = ee.ImageCollection(dataset).filterDate(f1, f2).select(bands)
        count = coll.size().getInfo()
        if count == 1:
            img = coll.first()
            muestra = img.sample(region=punto, scale=10000).first().toDictionary().getInfo()
            return muestra or {}
        elif count == 0:
            raise ValueError(f"{bands}: No se encontraron imágenes para el periodo de {f1} a {f2}.")
        else:
            raise ValueError(f"{bands}: El programa espera 1 imagen, pero se encontraron {count} entre {f1} y {f2}.")

    def get_values(self, var_name, dataset, bands, f1, f2, punto):
        muestra = self.get_sample(dataset, bands, f1, f2, punto)

        if var_name == 'velocidad viento':
            u = muestra.get(bands[0])
            v = muestra.get(bands[1])
            return (u**2 + v**2)**0.5 if u is not None and v is not None else None
        elif var_name == 'direccion viento':
            u = muestra.get(bands[0])
            v = muestra.get(bands[1])
            return (180 / math.pi) * math.atan2(v, u) if u is not None and v is not None else None
        elif var_name == 'humedad relativa':
            T  = muestra.get(bands[0])
            Td = muestra.get(bands[1])
            if T is not None and Td is not None:
                return 100 * (math.exp((17.625*Td)/(243.04+Td)) /
                              math.exp((17.625*T)/(243.04+T)))
            return None
        elif var_name == 'temperatura':
            kelvin = muestra.get(bands[0])
            return kelvin - 273.15 if kelvin is not None else None
        else:
            return muestra.get(bands[0]) if len(bands) == 1 else {b: muestra.get(b) for b in bands}

    def to_dataframe(self):
        results = self.fetch()
        if self.include_meta:
            punto = self.solicitud['punto']
            f1 = self.solicitud['fecha_inicio']
            lon, lat = punto['coordinates']
            results['fecha'] = f1.format('YYYY-MM-dd').getInfo()
            results['lat'] = lat
            results['lon'] = lon
        df = pd.DataFrame([results])
        return df
