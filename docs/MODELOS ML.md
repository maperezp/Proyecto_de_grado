# Preprocesamiento de Datos de Vibración y Modelamiento ML

Este documento explica el proceso completo de preprocesamiento de datos de vibración y desarrollo de modelos de machine learning para el análisis de fallas en maquinaria rotatoria implementado en el notebook `ML_DEVELOP.ipynb`.

[Link al dataset original](https://www02.smt.ufrj.br/~offshore/mfs/page_01.html)

## Estructura del Dataset Original

El dataset original se encuentra organizado en la siguiente estructura jerárquica:

```
dataset1/
├── normal/                     # Condición normal
│   ├── 10_Hz/
│   ├── 20_Hz/
│   └── 30_Hz/
├── horizontal-misalignment/     # Falla de desalineación horizontal
│   ├── 0.2mm/
│   ├── 0.4mm/
│   └── 0.6mm/
├── vertical-misalignment/       # Falla de desalineación vertical
│   ├── 0.2mm/
│   ├── 0.4mm/
│   └── 0.6mm/
├── imbalance/                  # Falla de desbalanceamiento
│   ├── 5g/
│   ├── 10g/
│   └── 15g/
├── underhang/                  # Fallas en rodamiento lado drive end (DE)
│   ├── cage_fault/
│   ├── ball_fault/
│   └── outer_race/
└── overhang/                   # Fallas en rodamiento lado no-drive end (NDE)
    ├── cage_fault/
    ├── ball_fault/
    └── outer_race/
```

## Datos de Sensores

Cada archivo CSV contiene datos de 8 canales de sensores:

1. **tachometer** - Tacómetro (referencia de velocidad)
2. **underhang-axial** - Vibración axial en rodamiento DE
3. **underhang-radial** - Vibración radial en rodamiento DE
4. **underhang-tangential** - Vibración tangencial en rodamiento DE
5. **overhang-axial** - Vibración axial en rodamiento NDE
6. **overhang-radial** - Vibración radial en rodamiento NDE
7. **overhang-tangential** - Vibración tangencial en rodamiento NDE
8. **microphone** - Señal de micrófono (eliminada en el preprocesamiento)

## Proceso de Preprocesamiento Implementado

### 1. Configuración del Entorno

El notebook utiliza las siguientes librerías principales:
- **Procesamiento de datos**: pandas, polars, numpy
- **Análisis estadístico**: scipy.stats, scipy.fft
- **Visualización**: matplotlib, seaborn, plotly
- **Machine Learning**: scikit-learn (versión verificada en el código)
- **Otras**: joblib, tqdm, pathlib

### 2. Extracción de Características

Se implementaron funciones para extraer características tanto en el dominio temporal como frecuencial:

#### Características en el Dominio del Tiempo (14 características):
Implementadas en la función `compute_basic_time_features()`:
- `mean` - Valor medio
- `std` - Desviación estándar  
- `rms` - Valor RMS (Root Mean Square)
- `max` - Valor máximo
- `min` - Valor mínimo
- `peak_to_peak` - Pico a pico
- `mean_abs` - Valor absoluto medio
- `crest_factor` - Factor de cresta
- `shape_factor` - Factor de forma
- `impulse_factor` - Factor de impulso
- `skewness` - Asimetría
- `kurtosis` - Curtosis
- `energy` - Energía total
- `zero_crossing_rate` - Tasa de cruces por cero

#### Características en el Dominio de la Frecuencia (14 características):
Implementadas en la función `compute_frequency_features()`:
- `dominant_freq` - Frecuencia dominante
- `dominant_amp` - Amplitud dominante
- `spectral_energy` - Energía espectral
- `spectral_centroid` - Centroide espectral
- `spectral_bandwidth` - Ancho de banda espectral
- `spectral_flatness` - Planitud espectral
- `F_mv` - Media del espectro
- `F_max` - Máximo del espectro
- `F_rms` - RMS del espectro
- `F_vr` - Varianza del espectro
- `F_sd` - Desviación estándar del espectro
- `F_sf` - Asimetría del espectro
- `F_kf` - Curtosis del espectro
- `F_rs` - Ratio máximo/media del espectro

### 3. Implementación de Submuestreo

Se implementó un sistema de submuestreo para generar datasets con diferentes frecuencias de muestreo:

- **Frecuencia base**: 50,000 Hz
- **Factores de submuestreo implementados**: [1, 2, 4, 8, 16, 32, 64]
- **Frecuencias resultantes**: [50,000, 25,000, 12,500, 6,250, 3,125, 1,563, 781] Hz

La función `downsample_dataframe()` implementa el submuestreo seleccionando cada n-ésima muestra.

### 4. Creación de Datasets por Configuración

#### Dataset de 3 Ejes (`data_3axis.csv`)
Se implementó la función `filer_columns()` para combinar datos de ambos rodamientos (underhang + overhang) en las tres direcciones:
- **Total de características**: 28 features por dirección × 3 direcciones = 84 features
- **Direcciones**: axial, radial, tangential
- **Sensores**: underhang (DE) + overhang (NDE)

#### Datasets por Dirección Individual 
Se implementó la función `filer_columns_dir()` para generar tres datasets separados:
1. **`data_axial.csv`** - Solo características de vibración axial
2. **`data_radial.csv`** - Solo características de vibración radial  
3. **`data_tangential.csv`** - Solo características de vibración tangencial

Cada dataset contiene **28 características** (14 temporales + 14 frecuenciales) por cada dirección.

## Pipeline de Modelamiento Implementado

### 1. Funciones Auxiliares Desarrolladas

Se implementaron las siguientes funciones de soporte:
- `create_preprocessor()`: Crea pipeline de preprocesamiento con imputación y escalado
- `split_data()`: División estratificada en train/validation/test (60%/20%/20%)
- `plot_confusion_matrix()`: Visualización de matrices de confusión
- `resultados_clasificacion_multiclase()`: Reportes detallados de clasificación

### 2. Pipeline Modular de Random Forest

Se desarrolló un pipeline completo con las siguientes etapas:

#### **Función `train_random_forest_pipeline()`**
Pipeline principal que ejecuta:
1. **Preprocesamiento**: Imputación de valores faltantes + StandardScaler
2. **División de datos**: Estratificada por clases con semilla fija (random_state=77)
3. **Modelo base**: Random Forest inicial (n_estimators=10, max_depth=3)
4. **Optimización progresiva**: GridSearchCV en dos fases
5. **Evaluación completa**: Métricas en train/validation/test
6. **Análisis de importancia**: Ranking de características más relevantes
7. **Persistencia**: Guardado de modelos en formato .joblib

#### **Optimización de Hiperparámetros**

Se implementaron dos estrategias:

**Estrategia Progresiva (`optimize_hyperparameters_progressive`)**:
- **Fase 1**: Parámetros principales (n_estimators, max_depth, class_weight)
- **Fase 2**: Refinamiento (min_samples_split, criterion)

**Estrategia Completa (`optimize_hyperparameters_full`)**:
- Grid search exhaustivo con todos los parámetros simultáneamente

**Parámetros optimizados**:
- `class_weight`: [None, 'balanced', 'balanced_subsample']
- `n_estimators`: [80, 100, 120]
- `max_depth`: [2, 4, 6, 8, 16]
- `min_samples_split`: [2, 3, 4, 5, 6]  
- `criterion`: ['entropy', 'gini', 'log_loss']

### 3. Ejecución Automatizada

#### **Función `run_dataset()`**
Procesa automáticamente cada dataset:
- Lee cada archivo CSV de la carpeta `ready/`
- Identifica frecuencias de muestreo disponibles
- Entrena modelo para cada frecuencia
- Guarda resultados intermedios en formato pickle

#### **Mapeo de Clases Implementado**
```python
dic_classes_num = {
    'normal': 0, 
    'horizontal-misalignment': 1, 
    'vertical-misalignment': 2,
    'imbalance': 3, 
    'ball_fault': 4, 
    'cage_fault': 5, 
    'outer_race': 6
}
```

### 4. Análisis de Resultados Implementado

#### **Extracción de Métricas**
La función `extract_performance_metrics()` recopila:
- Accuracy, Precision, Recall, F1-score (macro y weighted)
- Métricas por conjunto (train/validation/test)
- Análisis de overfitting (diferencia train-test)

#### **Análisis Estadístico**
Se implementaron pruebas estadísticas:
- **ANOVA de medidas repetidas**: Usando pingouin
- **Test de Friedman**: Alternativa no paramétrica
- **Pruebas post-hoc**: Comparaciones pareadas con corrección Bonferroni

#### **Visualizaciones Desarrolladas**
1. **Ranking de importancia de características**: Top 24 features globales
2. **Métricas vs frecuencia de muestreo**: Gráficos de línea por métrica
3. **Comparación por sensores**: Análisis separado por tipo de sensor
4. **Heatmap de accuracy**: Visualización bidimensional sensor x frecuencia
5. **Análisis por clase**: Desempeño individual para cada tipo de falla

#### **Comparación 3-ejes vs Sensores Individuales**
Se implementó análisis comparativo que determina:
- Mejor configuración con datos de 3 ejes
- Mejor configuración con sensores individuales
- Diferencias porcentuales de rendimiento
- Exportación a Excel para análisis posterior

## Modelos Generados

El proceso completo generó **80 modelos** entrenados:
- **4 configuraciones de sensores**: 3axis, axial, radial, tangential  
- **6 frecuencias de muestreo** por configuración: 50000, 25000, 12500, 6250, 3125, 1562 Hz
- **Formato**: Archivos .joblib optimizados para carga rápida
- **Nomenclatura**: `myRF_{sensor}_{frecuencia}.joblib`

## Estructura de Archivos Generados Real

```
data/
├── ready/                     # Datasets finales procesados
│   ├── data_3axis.csv        # Dataset combinado 3 ejes
│   ├── data_axial.csv        # Dataset solo axial
│   ├── data_radial.csv       # Dataset solo radial
│   └── data_tangential.csv   # Dataset solo tangencial
├── models/                   # Modelos entrenados (.joblib)
│   ├── myRF_3axis_{freq}.joblib
│   ├── myRF_axial_{freq}.joblib
│   ├── myRF_radial_{freq}.joblib
│   └── myRF_tangential_{freq}.joblib
├── results/                  # Resultados y métricas
│   ├── results_data_3axis.pkl
│   ├── results_data_axial.pkl
│   ├── results_data_radial.pkl
│   └── results_data_tangential.pkl
└── preprocess/              # Datos intermedios de procesamiento
    └── sampling_rate/       # Datos agrupados por frecuencia
        ├── data_50000.csv
        ├── data_25000.csv
        └── data_samplings.csv
```

## Métricas de Evaluación

Los modelos se evaluaron usando:
- **Accuracy**: Precisión general del modelo
- **Precision macro**: Promedio de precision por clase
- **Recall macro**: Promedio de recall por clase  
- **F1-score macro**: Promedio armónico de precision y recall
- **Matriz de confusión**: Análisis detallado por clase
- **Análisis de overfitting**: Diferencia entre accuracy de entrenamiento y test