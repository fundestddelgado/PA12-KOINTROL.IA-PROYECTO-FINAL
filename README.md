# ☀️ "Modelo de red neuronal para la predicción de radiación solar en Panamá usando variables climáticas.(MRNS)"

**MRNS** es una aplicación de escritorio desarrollada en **Python** cuyo objetivo principal es predecir la radiación solar neta en Panamá a nivel de corregimiento, utilizando datos climáticos procesados por una Red Neuronal (NN).

---

##  Descripción General

El proyecto aborda la pregunta clave: **"¿Cómo afecta el clima a la generación de paneles solares?"**

Para responder a esto, el sistema se enfoca en:
1.  **Mapear** todo el país con datos climáticos por coordenadas.
2.  Utilizar un **modelo de Red Neuronal** entrenado para predecir la radiación solar neta (variable clave para la generación de energía fotovoltaica).
3.  **Visualizar** los resultados a nivel de corregimiento en un mapa interactivo.

La aplicación integra la visualización de los resultados del modelo con una interfaz moderna y funcionalidades de predicción por punto geográfico (futura implementación).

---

##  Arquitectura y Flujo de Datos

El proyecto se estructura en tres fases principales: **Datos**, **Modelo** e **Interfaz**.

## 📝 Recopilación y Variables del Estudio

### 1. Recopilación y Procesamiento de Datos

* **Fuente de Datos:** La información climática (múltiples variables) se recopiló utilizando **Google Earth Engine** y el *dataset* **AgEra5**.
* **Volumen:** Se integró un *dataset* de **128,000 puntos de datos** (128k).
* **Procesamiento:** Los datos fueron procesados, limpiados e integrados en un solo *dataset* por píxel, utilizando sus coordenadas de latitud y longitud.
    * Este *dataset* es utilizado por el módulo de mapeo para generar estadísticas por corregimiento.

---

### . Variables Utilizadas en el Estudio

Las siguientes variables climáticas fueron extraídas, procesadas y utilizadas como *features* (características) para el análisis y modelado del estudio. 

| Variable | Tipo de Dato | Propósito/Porqué Simple |
| :--- | :--- | :--- |
| **date** | Categórica (Fecha) | Permite la indexación y el análisis temporal. |
| **lon** | Numérica (Coordenada) | Define la ubicación espacial (Longitud). |
| **lat** | Numérica (Coordenada) | Define la ubicación espacial (Latitud). |
| **elevation** | Numérica (Metros) | Representa la altitud, que influye directamente en el clima. |
| **Cloud\_Cover\_Mean\_24h** | Numérica (Fracción) | Mide la nubosidad promedio, afectando la radiación solar. |
| **Temperature\_Air\_2m\_Mean\_24h** | Numérica (Kelvin) | Temperatura del aire a 2m (promedio de 24h), crucial para el clima. |
| **Temperature\_Air\_2m\_Mean\_24h\_C** | Numérica (Celsius) | Versión de la temperatura en Celsius para fácil interpretación. |
| **relative\_humidity** | Numérica (%) | Mide la cantidad de vapor de agua en el aire. |
| **surface\_pressure** | Numérica (Pascal) | Presión en la superficie terrestre, afecta sistemas meteorológicos. |
| **temperature\_2m\_C** | Numérica (Celsius) | Temperatura del aire a 2m (instantánea/diaria), un factor clave. |
| **total\_precipitation\_sum** | Numérica (Metros) | Cantidad acumulada de lluvia/nieve, esencial para modelos climaticos. |
| **surface\_net\_solar\_radiation\_sum (target)** | Numérica ($J/m^2$) | Es la **variable objetivo** (a predecir/analizar), representa la energía solar neta recibida. |

---

### 2. Modelo de Red Neuronal (NN)

Se utilizó **TensorFlow/Keras** para construir y entrenar una Red Neuronal densa.

* **Arquitectura del Modelo (`build_model`)**:

    | Capa / Bloque | Tipo de Capa | Unidades | Regularización / Dropout | Función de Activación | Notas |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | **Inicial** | `Dense` + `BatchNormalization` | 128 | `l2(1e-6)` | `gelu` | Entrada con `input_shape` |
    | **Bloque 1** | `Dense` + `BatchNormalization` + `Dropout` | 256 | `l2(1e-6)` | `gelu` | `Dropout(0.1)` |
    | **Bloque 2 (Residual-like)** | `Dense` + `BatchNormalization` | 256 | `l2(1e-6)` | `gelu` | |
    | | `Dense` + `BatchNormalization` + `Dropout` | 128 | `l2(1e-6)` | `gelu` | `Dropout(0.05)` |
    | **Bloque Final** | `Dense` | 64, 32 | N/A | `gelu` | |
    | **Salida** | `Dense` | 1 | N/A | Lineal | Predicción de radiación |

* **Compilación:**
    * **Optimizador:** `tf.keras.optimizers.Adam(learning_rate=0.0003)`
    * **Función de Pérdida (Loss):** `mse` (Error Cuadrático Medio)
    * **Métrica Principal:** `mae` (Error Absoluto Medio)

* **Métricas de Rendimiento (Reales):**

    * **MAE real:** 334,064.76 MJ/m²/día
    * **RMSE real:** 479,379.42 MJ/m²/día
    * **R² real:** 0.9806
    * **MAPE (%):** 32.41%

### 3. Interfaz de Usuario (UI) y Visualización

La aplicación utiliza **Tkinter** para la interfaz de escritorio, organizada en pestañas para una navegación clara.

* **Pestaña 1: Mapa por Corregimiento**
    * Utiliza **Plotly Express** y **GeoPandas** para generar un mapa interactivo de Panamá, coloreando los corregimientos según la radiación promedio predicha.
    * Debido a problemas de renderizado de Tkinter, el mapa se **cachea** (para reducir la latencia de procesamiento) y se **abre automáticamente en el navegador web** para garantizar la interactividad (zoom, hover).
* **Pestaña 2: Predictor por Coordenadas**
    * Diseñada para ingresar latitud y longitud.
    * **Estado Actual:** Actúa como un *placeholder* (marcador de posición). Los valores de radiación mostrados son **generados artificialmente** para demostrar la funcionalidad del resultado, ya que la integración de la inferencia del modelo se agregará más adelante en la Hackathon.
---

##  Estructura y Módulos Principales

El proyecto sigue una estructura modular para facilitar el desarrollo y mantenimiento:

* **`app_unified.py`** → Control central de la aplicación y gestión de la interfaz de usuario unificada (Pestañas de Predictor y Mapa).
* **`Visualization/corregimientos_map.py`** → Módulo encargado de la lógica de carga de GeoJSON, el procesamiento GeoPandas/Pandas y la generación/caching del mapa interactivo de Plotly.
* **`Datasets/`** → Carpeta que almacena los archivos de datos requeridos: `solar_with_predictions.csv` (datos procesados y predicciones) y `Panama_Boundaries.geojson` (límites geográficos).
* **`solar_radiation_map_cache.html`** → Archivo HTML generado y cacheado por Plotly para la visualización del mapa.

---

##  Librerías Utilizadas

El proyecto se basa en las siguientes librerías de Python:

| Librería | Función Principal |
| :--- | :--- |
| **tkinter** | Interfaz gráfica de escritorio (UI principal) |
| **pandas** | Manejo y análisis de datos (.csv) |
| **geopandas** | Manejo de datos geoespaciales y operaciones de unión espacial (`sjoin`) |
| **plotly.express** | Generación de mapas interactivos choropleth (Web) |
| **pathlib** | Manejo robusto de rutas de archivos (clave para evitar errores `FileNotFound`) |
| **tensorflow / keras** | Desarrollo y entrenamiento del modelo de Red Neuronal |
| **numpy** | Manejo numérico y cálculo de promedios |

---

##  Futuras Mejoras

* **Integración en Tiempo Real:** Conexión del módulo de predicción por coordenadas (Pestaña 2) con el modelo de Red Neuronal real para obtener resultados en la interfaz.
* **Integración Web:** Explorar opciones para incrustar el mapa interactivo directamente en la interfaz de escritorio sin depender del navegador externo (ej. utilizando QtWebEngine o webview).
* **Análisis Temporal:** Permitir la selección de fechas o períodos de tiempo para la predicción.

---

## 👥 Equipo de Desarrollo (SIC 2025 - PA12)

| Nombre | Rol o Función |
| :--- | :--- |
| **Alan Sánchez** | Líder de Proyecto / Desarrollador Principal (Modelo NN y UI) |
| **Abdiel Bernal** | Desarrollador de Visualización de Datos (Mapeo GeoPandas/Plotly) |
| **Ernesto Jurado** | Desarrollador de la Interfaz de Usuario (Tkinter/Funcionalidades Predictor) |
| **Ana Flores** | Desarrolladora de la Base de Datos y Documentación (Procesamiento de Datos) |

---

## ©️ Créditos

Proyecto desarrollado como parte del programa **Samsung Innovation Campus (SIC) 2025** - Región de Panamá.