# Docker ML App <!-- omit in toc -->

Documentación técnica de la aplicación web desarrollada con FastAPI y Docker para el monitoreo en tiempo real de dispositivos PCH-Cloud. La aplicación integra análisis de machine learning para detección predictiva de fallas en rodamientos y gestión de conectividad WiFi para dispositivos embebidos.

## Tabla de contenido 
- [Arquitectura Técnica](#arquitectura-técnica)
  - [Stack Tecnológico](#stack-tecnológico)
  - [Estructura del Proyecto](#estructura-del-proyecto)
- [Aplicación Principal (`app.py`)](#aplicación-principal-apppy)
  - [API Endpoints](#api-endpoints)
    - [Sistema](#sistema)
    - [Dispositivos](#dispositivos)
    - [Grabaciones](#grabaciones)
    - [Predicciones](#predicciones)
    - [Análisis de Señales](#análisis-de-señales)
    - [Conectividad WiFi](#conectividad-wifi)
- [Componentes Principales](#componentes-principales)
  - [Módulos Principales (`src/modules/)`](#módulos-principales-srcmodules)
    - [**Cliente PCH-Cloud** (`pch_client.py`)](#cliente-pch-cloud-pch_clientpy)
    - [**Motor de Predicciones** (`model_predictor.py`)](#motor-de-predicciones-model_predictorpy)
    - [**Generador de Gráficos** (`plot_utils.py`)](#generador-de-gráficos-plot_utilspy)
    - [**Base de Datos** (`prediction_db.py`)](#base-de-datos-prediction_dbpy)
    - [**Gestor de WiFi** (`wifi.py`)](#gestor-de-wifi-wifipy)
  - [Interfaz Web](#interfaz-web)
    - [**Dashboard Principal** (`static/dashboard.html`)](#dashboard-principal-staticdashboardhtml)
    - [**Configuración WiFi** (`static/wifi-config.html`)](#configuración-wifi-staticwifi-confightml)
  - [Modelos de Machine Learning](#modelos-de-machine-learning)
    - [Tipos de Modelos](#tipos-de-modelos)
    - [Clases de Predicción](#clases-de-predicción)
- [Configuración del Contenedor - Pruebas locales](#configuración-del-contenedor---pruebas-locales)
  - [Prerrequisitos](#prerrequisitos)
  - [Construcción de la Imagen](#construcción-de-la-imagen)
  - [Ejecución del Contenedor](#ejecución-del-contenedor)
  - [Acceso a la Aplicación](#acceso-a-la-aplicación)
    - [**Interfaces Web**](#interfaces-web)
    - [**Pruebas con API REST**](#pruebas-con-api-rest)
  - [Gestión del Contenedor](#gestión-del-contenedor)
    - [**Operaciones Básicas**](#operaciones-básicas)
    - [**Limpieza del Sistema**](#limpieza-del-sistema)
- [Despliegue](#despliegue)


## Objetivo

La aplicación del directorio `docker-ml-app-deploy` proporciona una plataforma integral de monitoreo predictivo que incluye:

- **Monitoreo en tiempo real** de sensores de vibración en equipos industriales.
- **Análisis predictivo** mediante modelos de machine learning para detección temprana de fallas.
- **Visualización interactiva** de señales y datos con gráficos en tiempo real.
- **Gestión de conectividad WiFi** para dispositivos embebidos y sistemas IoT.
- **Almacenamiento persistente** y consulta de historial de predicciones.

# Arquitectura Técnica

## Stack Tecnológico

- **Backend**: FastAPI (Framework web moderno y rápido)
- **Frontend**: HTML5, JavaScript ES6+, Bootstrap 5
- **Base de Datos**: SQLite (Base de datos embebida)
- **Machine Learning**: Modelos Random Forest entrenados con scikit-learn 1.7.0 (formato .joblib)
- **Visualización**: Plotly.js (Gráficos interactivos)
- **Contenedores**: Docker (Despliegue multiplataforma)
- **Redes**: NetworkManager, wpa_supplicant (Gestión WiFi)

## Estructura del Proyecto

```
docker-ml-app-deploy/
├── dockerfile                 # Configuración del contenedor Docker
├── requirements.txt          # Dependencias de Python
├── README.md                # Documentación principal del proyecto
├── DEPLOY-SYMPHONY-BOARD.md # Guía de despliegue en Symphony Board
└── src/                     # Código fuente de la aplicación
    ├── app.py              # Aplicación principal FastAPI
    ├── static/             # Archivos web estáticos (frontend)
    │   ├── dashboard.html  # Interfaz principal del dashboard
    │   ├── dashboard.js    # Lógica JavaScript del dashboard
    │   ├── wifi-config.html # Interfaz de configuración WiFi
    │   ├── wifi-config.js   # Lógica JavaScript para WiFi
    │   └── style.css       # Estilos CSS personalizados
    ├── modules/            # Módulos Python reutilizables
    │   ├── pch_client.py   # Cliente para API PCH-Cloud
    │   ├── model_predictor.py # Motor de predicciones ML
    │   ├── plot_utils.py   # Utilidades para generación de gráficos
    │   ├── prediction_db.py # Gestión de base de datos SQLite
    │   ├── wifi.py         # Gestión de conectividad WiFi
    │   └── common.py       # Utilidades y funciones comunes
    ├── models/             # Modelos de ML pre-entrenados
    │   ├── myRF_3axis_50000.joblib      # Modelo para análisis 3-ejes
    │   ├── myRF_axial_50000.joblib      # Modelo para eje axial
    │   ├── myRF_radial_50000.joblib     # Modelo para eje radial
    │   └── myRF_tangential_50000.joblib # Modelo para eje tangencial
    └── db/                 # Base de datos local
        └── predictions.db  # Almacenamiento de predicciones
```



# Aplicación Principal (`app.py`)

La aplicación FastAPI proporciona una API RESTful completa organizada por módulos funcionales. Los endpoints están agrupados por categorías para facilitar su uso y mantenimiento:

```python
# Endpoints principales de la API:
# - Sistema: /api/status, /api/models
# - Dispositivos: /api/devices/*
# - Grabaciones: /api/recordings/*
# - Predicciones: /api/predict/*
# - Análisis de señales: /api/signal/*
# - Conectividad WiFi: /api/wifi/*
```


## API Endpoints

### Sistema
- `GET /api/status` - Obtiene el estado general de la aplicación y servicios
- `GET /api/models` - Lista los modelos de ML disponibles y sus metadatos

### Dispositivos
- `GET /api/devices` - Recupera la lista de dispositivos PCH-Cloud conectados
- `GET /api/devices/{device_id}` - Obtiene información detallada de un dispositivo específico

### Grabaciones
- `POST /api/recordings/{device_id}/period` - Recupera datos de grabaciones por período de tiempo
- `GET /api/recordings/{device_id}/{recording_id}/samples` - Obtiene muestras específicas de una grabación

### Predicciones
- `POST /api/predict/period` - Ejecuta predicciones de ML para un período específico
- `GET /api/predictions/recent` - Recupera las predicciones más recientes del historial
- `DELETE /api/predictions/{prediction_id}` - Elimina una predicción específica del historial

### Análisis de Señales
- `POST /api/signal/period/{device_id}` - Realiza análisis de señales en dominio temporal y frecuencial

### Conectividad WiFi
- `POST /api/wifi/connect` - Conecta el dispositivo a una red WiFi específica
- `GET /api/wifi/status` - Obtiene el estado actual de la conexión WiFi
- `GET /api/wifi/scan` - Escanea las redes WiFi disponibles en el entorno


# Componentes Principales

## Módulos Principales [(`src/modules/)`](/docker-ml-app-deploy/src/modules/)

### **Cliente PCH-Cloud** (`pch_client.py`)
- **Autenticación**: Gestión de credenciales y tokens de acceso
- **Sesiones**: Mantenimiento de sesiones activas con la API PCH-Cloud
- **Datos**: Recuperación de información de dispositivos y grabaciones históricas

### **Motor de Predicciones** (`model_predictor.py`)
- **Carga de Modelos**: Gestión de modelos Random Forest pre-entrenados
- **Extracción de Características**: Procesamiento de señales para análisis ML
- **Predicción**: Predicción de fallas en sistemas con rodamientos

### **Generador de Gráficos** (`plot_utils.py`)
- **Visualización Interactiva**: Generación de gráficos con Plotly.js
- **Análisis FFT**: Transformada rápida de Fourier para análisis frecuencial
- **Estadísticas**: Cálculo de métricas estadísticas de señales

### **Base de Datos** (`prediction_db.py`)
- **Gestión SQLite**: Operaciones CRUD para almacenamiento local
- **Historial**: Mantenimiento de registros de predicciones y resultados

### **Gestor de WiFi** (`wifi.py`)
- **Escaneo**: Detección de redes WiFi disponibles
- **Status**: monitoreo del estado de la conexión de red
- **Conexión**: Conexión a nuevas redes.

## Interfaz Web

### **Dashboard Principal** (`static/dashboard.html`)
- **Selección de Dispositivos**: Interfaz para elegir equipos monitoreados de pch.
- **Control Temporal**: Definición de períodos de análisis y consulta
- **Ejecución de Predicciones**: Botones y controles para iniciar análisis ML
- **Visualización de Resultados**: Gráficos interactivos.

### **Configuración WiFi** (`static/wifi-config.html`)
- **Escaneo de Redes**: Lista actualizada de redes WiFi disponibles
- **Formulario de Conexión**: Interfaz segura para introducir credenciales
- **Monitor de Estado**: Indicadores visuales del estado de conectividad
- **Gestión de Conexiones**: Herramientas para administrar redes guardadas


## Modelos de Machine Learning

### Tipos de Modelos

Los modelos de machine learning se almacenan como objetos serializados en formato `.joblib` y están ubicados en el directorio [`src/models/`](/docker-ml-app-deploy/src/models/). Cada modelo fue entrenado usando scikit-learn 1.7.0:

1. **`myRF_3axis_50000.joblib`**: Modelo integral para análisis combinado de los tres ejes (X, Y, Z).
2. **`myRF_axial_50000.joblib`**: Modelo especializado para análisis del eje axial.
3. **`myRF_radial_50000.joblib`**: Modelo especializado para análisis del eje radial. 
4. **`myRF_tangential_50000.joblib`**: Modelo especializado para análisis del eje tangencial.

### Clases de Predicción

El sistema puede identificar las siguientes condiciones operativas y tipos de fallas:

- **`normal`**: Funcionamiento normal del equipo sin anomalías detectadas
- **`horizontal-misalignment`**: Desalineación horizontal del eje de rotación
- **`vertical-misalignment`**: Desalineación vertical del eje de rotación
- **`imbalance`**: Desbalance en el rotor o elementos giratorios
- **`ball_fault`**: Falla en las bolas o elementos rodantes del rodamiento
- **`cage_fault`**: Falla en la jaula o separador del rodamiento
- **`outer_race`**: Falla en la pista externa del rodamiento



# Configuración del Contenedor - Pruebas locales

## Prerrequisitos

- **Docker**: Versión 20.10 o superior instalada
- **Sistema Operativo**: Linux (recomendado) o Windows con WSL2
- **Git**: Para clonar el repositorio
- **Permisos**: Acceso sudo para configuraciones de red (si se requiere WiFi)

nota: está guia fue elaborada con Docker version 27.5.1, build 27.5.1-0ubuntu3~22.04.2

## Construcción de la Imagen

```bash
# Clonar el repositorio del proyecto
git clone [repository-url]
cd docker-ml-app-deploy

# Construir imagen para PC local (AMD64)
docker build --build-arg TARGETPLATFORM=linux/amd64 -t ml-app:amd64 .

```

## Ejecución del Contenedor

```bash
# Ejecutar contenedor en modo daemon con configuración de red
docker run -d \
  --name ml-app-container \
  --network=host \
  --privileged \
  -p 8080:8080 \
  ml-app:amd64

# Verificar que el contenedor está ejecutándose
docker ps
```

> **Nota**: Para la gestión WiFi, el contenedor requiere privilegios especiales:
> - `--network=host`: Acceso completo a las interfaces de red del host
> - `--privileged`: Permisos elevados para configuración de red
> - `-p 8080:8080`: Mapeo de puerto (opcional con --network=host)

## Acceso a la Aplicación

Una vez que el contenedor está en ejecución, puede acceder a la aplicación a través de múltiples interfaces:

### **Interfaces Web**
- **Dashboard Principal**: [http://localhost:8080](http://localhost:8080)
- **Documentación API**: [http://localhost:8080/docs](http://localhost:8080/docs) (Swagger UI)
- **Configuración WiFi**: [http://localhost:8080/wifi](http://localhost:8080/wifi)
- **API Alternativa**: [http://localhost:8080/redoc](http://localhost:8080/redoc) (ReDoc)

### **Pruebas con API REST**

```bash
# Verificar estado de la aplicación
curl http://localhost:8080/api/status

# Comprobar estado de WiFi
curl http://localhost:8080/api/wifi/status

# Escanear redes WiFi disponibles
curl http://localhost:8080/api/wifi/scan

# Listar modelos de ML disponibles
curl http://localhost:8080/api/models

# Obtener dispositivos conectados
curl http://localhost:8080/api/devices
```

## Gestión del Contenedor

### **Operaciones Básicas**

```bash
# Detener el contenedor
docker stop ml-app-container

# Reiniciar el contenedor
docker restart ml-app-container

# Ver logs del contenedor
docker logs ml-app-container

# Acceder al shell del contenedor
docker exec -it ml-app-container /bin/bash
```

### **Limpieza del Sistema**

```bash
# Eliminar el contenedor (debe estar detenido)
docker stop ml-app-container
docker rm ml-app-container

# Eliminar la imagen
docker rmi ml-app:amd64

# Limpiar imágenes no utilizadas
docker image prune -f
```

# Despliegue

Para el despliegue en la Symphony Board u otros dispositivos embebidos ARM64, consulte la guía completa de despliegue disponible en:

📖 **[Guía de Despliegue en Symphony Board](/docs/DESPLIEGUE_SYMPHONY_BOARD.md)**

Esta guía incluye:
- Configuración de red entre PC host y Symphony Board
- Transferencia de imágenes Docker via SSH/SCP  
- Configuración específica para arquitectura ARM64

