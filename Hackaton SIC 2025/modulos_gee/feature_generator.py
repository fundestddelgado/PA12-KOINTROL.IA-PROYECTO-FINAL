'''
Función para generar datos de entrada para el modelo
de predcción para una coordenada en específico
'''
'''Orden segun solar_merged_clean.csv
Cloud_Cover_Mean_24h,
date,
lon,
lat,
elevation,
relative_humidity,
surface_net_solar_radiation_sum,
surface_pressure,
temperature_2m_C
total_precipitation_sum,
wind_direction,
wind_speed'''

from classfinal import Solicitud, DataFetcher
def feature_generator(coords):
    # Variables
    vars = [
        'nubosidad',
        'elevacion',
        'humedad relativa',
        'radiacion solar',
        'presion',
        'temperatura',
        'precipitacion',
        'direccion viento',
        'velocidad viento'
    ]
    
    # Hacer una solicitud
    solicitud_class = Solicitud(coords)
    detalles = solicitud_class.hacer_solicitud(vars)
    
    # Usar Fetcher y generar DataFrame
    fetcher = DataFetcher(detalles)
    df = fetcher.to_dataframe()
    
    # Renombrar columnas
    column_map = {
        'nubosidad': 'Cloud_Cover_Mean_24h',
        'fecha': 'date',
        'lon': 'lon',
        'lat': 'lat',
        'elevacion': 'elevation',
        'humedad relativa': 'relative_humidity',
        'radiacion solar': 'surface_net_solar_radiation_sum',
        'presion': 'surface_pressure',
        'temperatura': 'temperature_2m_C',
        'precipitacion': 'total_precipitation_sum',
        'direccion viento': 'wind_direction',
        'velocidad viento': 'wind_speed'
    }
    df = df.rename(columns=column_map)
    
    # Reordenar columnas
    desired_order = [
        'Cloud_Cover_Mean_24h',
        'date',
        'lon',
        'lat',
        'elevation',
        'relative_humidity',
        'surface_net_solar_radiation_sum',
        'surface_pressure',
        'temperature_2m_C',
        'total_precipitation_sum',
        'wind_direction',
        'wind_speed'
    ]
    df = df[desired_order]
    
    return df
# DEMO
# print(feature_generator([-99.1332, 19.4326]))
