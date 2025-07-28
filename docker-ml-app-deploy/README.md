# PCH-Cloud Real-Time Monitoring Application

Una aplicación web completa construida con FastAPI y Docker para el monitoreo en tiempo real de dispositivos PCH-Cloud, con análisis de machine learning integrado y gestión de conectividad WiFi.

## 🎯 Objetivo

Proporcionar una plataforma integral para:
- Monitoreo en tiempo real de sensores de vibración
- Análisis predictivo usando modelos de machine learning
- Visualización interactiva de señales y datos
- Gestión de conectividad WiFi en dispositivos embebidos
- Almacenamiento y consulta de historial de predicciones

## 🏗️ Arquitectura Técnica

### Stack Tecnológico
- **Backend**: FastAPI 
- **Frontend**: HTML5, JavaScript, Bootstrap 5
- **Database**: SQLite
- **ML**: scikit-learn, Random Forest
- **Visualización**: Plotly.js
- **Containerización**: Docker
- **Networking**: NetworkManager, wpa_supplicant

### Componentes Principales

#### 1. Aplicación Principal (`app.py`)
```python
# FastAPI application con endpoints para:
- Sistema: /api/status, /api/models
- Dispositivos: /api/devices/*
- Grabaciones: /api/recordings/*
- Predicciones: /api/predict/*
- Señales: /api/signal/*
- WiFi: /api/wifi/*
```

#### 2. Módulos Core

**PCH Client (`modules/pch_client.py`)**
- Autenticación con PCH-Cloud API
- Gestión de sesiones y tokens
- Recuperación de datos de dispositivos y grabaciones

**Model Predictor (`modules/model_predictor.py`)**
- Carga de modelos Random Forest pre-entrenados
- Extracción de características de señales
- Predicción de fallas en rodamientos

**Plot Generator (`modules/plot_utils.py`)**
- Generación de gráficos interactivos con Plotly
- Análisis FFT y dominio del tiempo
- Cálculo de estadísticas de señal

**Prediction Database (`modules/prediction_db.py`)**
- Gestión de base de datos SQLite
- Almacenamiento de predicciones e historial
- Consultas optimizadas

**WiFi Manager (`modules/wifi.py`)**
- Escaneo de redes WiFi disponibles
- Conexión automática con múltiples métodos
- Monitoreo de estado de conectividad

#### 3. Interface Web

**Dashboard Principal (`static/dashboard.html`)**
- Selección de dispositivos y períodos
- Ejecución de predicciones
- Visualización de resultados
- Análisis de señales interactivo

**Configuración WiFi (`static/wifi-config.html`)**
- Escaneo de redes disponibles
- Formulario de conexión
- Estado de conectividad en tiempo real

## 🚀 Guía de Instalación

### Método 1: Docker (Recomendado)

```bash
# 1. Construir la imagen
docker build -t pch-monitoring .

# 2. Ejecutar con privilegios de red (requerido para WiFi)
docker run -d \
  --name pch-monitoring \
  --network=host \
  --privileged \
  -v /var/run/docker.sock:/var/run/docker.sock \
  pch-monitoring

# 3. Verificar que está ejecutándose
docker logs pch-monitoring
```

### Método 2: Desarrollo Local

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar PCH-Cloud (opcional)
mkdir -p config
echo '{"username": "user", "password": "pass"}' > config/config.json

# 3. Ejecutar aplicación
cd src && python app.py
```

## 🔧 Configuración

### Variables de Entorno

```bash
# Configuración Python
PYTHONDONTWRITEBYTECODE=1  # No crear archivos .pyc
PYTHONUNBUFFERED=1         # Output sin buffer

# Configuración de aplicación
APP_HOST=0.0.0.0          # Host de la aplicación
APP_PORT=8080             # Puerto de la aplicación
DEBUG_MODE=false          # Modo debug
```

### Archivos de Configuración

**config/config.json** (PCH-Cloud credentials)
```json
{
  "username": "tu_usuario",
  "password": "tu_password"
}
```

**config/hosts.json** (PCH-Cloud servers)
```json
{
  "api_base_url": "https://api.pch-cloud.com",
  "timeout": 30
}
```

## 📡 API Reference

### Endpoints del Sistema

#### GET /api/status
Retorna el estado general de la aplicación.

**Response:**
```json
{
  "application": "PCH-Cloud Real-Time Monitoring",
  "version": "1.0.0",
  "status": "running",
  "pch_cloud": {
    "connected": true,
    "host": "api.pch-cloud.com"
  },
  "models": {
    "loaded": 4,
    "available": ["myRF_3axis_50000", "myRF_axial_50000", ...]
  },
  "database": {
    "total_predictions": 1234,
    "file_size_mb": 5.2
  }
}
```

#### GET /api/models
Lista los modelos de ML disponibles.

**Response:**
```json
{
  "models": [
    "myRF_3axis_50000",
    "myRF_axial_50000", 
    "myRF_radial_50000",
    "myRF_tangential_50000"
  ]
}
```

### Endpoints de Predicción

#### POST /api/predict/period
Realiza predicciones para un período de tiempo específico.

**Request:**
```json
{
  "device_id": "device_001",
  "model_name": "myRF_3axis_50000",
  "period": {
    "period_type": "last_24h",
    "hours_back": 24
  },
  "channel": 1
}
```

**Response:**
```json
{
  "device_id": "device_001",
  "model_used": "myRF_3axis_50000",
  "predictions": [
    {
      "recording_id": "rec_123",
      "timestamp": "2025-07-21T12:00:00Z",
      "prediction": {
        "prediction": "normal",
        "probabilities": {"normal": 0.95, "imbalance": 0.05}
      },
      "success": true
    }
  ],
  "summary": {
    "total_recordings": 10,
    "successful_predictions": 9,
    "most_common_prediction": {
      "class": "normal",
      "percentage": 90
    }
  }
}
```

### Endpoints de Análisis de Señales

#### POST /api/signal/period/{device_id}
Genera análisis de señal para un período específico.

**Request:**
```json
{
  "period": {
    "period_type": "last_hour",
    "hours_back": 1
  },
  "channel": 1
}
```

**Response:**
```json
{
  "time_plot": {
    "data": [...],
    "layout": {...}
  },
  "fft_plot": {
    "data": [...],
    "layout": {...}
  },
  "stats": {
    "rms": 0.123,
    "peak": 0.456,
    "sampling_rate": 25000
  }
}
```

### Endpoints WiFi

#### GET /api/wifi/scan
Escanea redes WiFi disponibles.

**Response:**
```json
{
  "success": true,
  "networks": {
    "status": "success",
    "networks": [
      {
        "ssid": "Mi_Red_WiFi",
        "signal": "75",
        "security": "WPA2",
        "method": "nmcli"
      }
    ]
  }
}
```

#### POST /api/wifi/connect
Conecta a una red WiFi específica.

**Request:**
```json
{
  "ssid": "Mi_Red_WiFi",
  "password": "mi_password"
}
```

**Response:**
```json
{
  "success": true,
  "message": "WiFi connection attempt initiated",
  "status": {
    "status": "success",
    "message": "Connected to Mi_Red_WiFi using nmcli",
    "method": "nmcli"
  }
}
```

#### GET /api/wifi/status
Obtiene el estado actual de la conexión WiFi.

**Response:**
```json
{
  "success": true,
  "status": {
    "connected": true,
    "ssid": "Mi_Red_WiFi",
    "ip_address": "192.168.1.100"
  }
}
```

## 🤖 Modelos de Machine Learning

### Arquitectura de Modelos

La aplicación incluye 4 modelos Random Forest pre-entrenados:

1. **myRF_3axis_50000.joblib**: Modelo combinado para análisis de 3 ejes
2. **myRF_axial_50000.joblib**: Especializado en eje axial
3. **myRF_radial_50000.joblib**: Especializado en eje radial  
4. **myRF_tangential_50000.joblib**: Especializado en eje tangencial

### Clases de Predicción

```python
CLASS_NAMES = {
    0: 'normal',
    1: 'horizontal-misalignment', 
    2: 'vertical-misalignment',
    3: 'imbalance',
    4: 'ball_fault',
    5: 'cage_fault',
    6: 'outer_race'
}
```

### Extracción de Características

**Dominio del Tiempo:**
- RMS (Root Mean Square)
- Valor pico
- Curtosis (kurtosis)
- Asimetría (skewness)
- Media y desviación estándar

**Dominio de la Frecuencia:**
- Frecuencia dominante
- Amplitud dominante
- Energía espectral
- Centroide espectral
- Ancho de banda espectral

### Uso de Modelos

```python
# Ejemplo de uso del predictor
predictor = ModelPredictor()
prediction = predictor.predict(
    data=samples_data,
    model_name="myRF_3axis_50000"
)
```

## 🖥️ Interface de Usuario

### Dashboard Principal

**Funcionalidades:**
- Selector de dispositivos conectados
- Configuración de períodos de análisis
- Selección de modelo de ML
- Ejecución de predicciones
- Visualización de resultados en tabla
- Análisis de señales con gráficos interactivos

**Períodos Disponibles:**
- Último minuto
- Última hora  
- Últimas 24 horas
- Período personalizado

### Configuración WiFi

**Funcionalidades:**
- Estado actual de conexión
- Escaneo automático de redes
- Conexión a redes abiertas y seguras
- Indicadores de intensidad de señal
- Formulario de conexión manual

## 🗄️ Base de Datos

### Esquema de Tablas

**predictions**
```sql
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    device_name TEXT,
    recording_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    channel INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    prediction_class TEXT,
    probabilities TEXT,
    confidence REAL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    created_at TEXT NOT NULL
);
```

### Operaciones Principales

```python
# Guardar predicción
prediction_db.save_prediction(
    device_id="device_001",
    recording_id="rec_123", 
    model_name="myRF_3axis_50000",
    prediction_result=result,
    success=True
)

# Obtener predicciones recientes
recent = prediction_db.get_recent_predictions(limit=50)

# Obtener predicciones por dispositivo
device_preds = prediction_db.get_predictions_by_device("device_001")
```

## 🔧 Desarrollo y Testing

### Estructura del Proyecto

```
src/
├── app.py                 # Aplicación principal FastAPI
├── modules/               # Módulos Python
│   ├── __init__.py
│   ├── pch_client.py     # Cliente PCH-Cloud
│   ├── model_predictor.py # Predictor ML
│   ├── plot_utils.py     # Utilidades gráficos
│   ├── prediction_db.py  # Base de datos
│   ├── wifi.py          # Gestión WiFi
│   └── common.py        # Utilidades comunes
├── static/              # Archivos web estáticos
│   ├── dashboard.html   # Dashboard principal
│   ├── dashboard.js     # Lógica JavaScript
│   ├── wifi-config.html # Configuración WiFi
│   ├── wifi-config.js   # Lógica WiFi
│   └── style.css        # Estilos CSS
├── models/              # Modelos ML pre-entrenados
│   └── *.joblib
└── db/                  # Base de datos local
    └── predictions.db
```

### Comandos de Desarrollo

```bash
# Instalar dependencias de desarrollo
pip install -r requirements.txt

# Ejecutar con auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8080

# Verificar modelos ML
python -c "from modules.model_predictor import ModelPredictor; mp = ModelPredictor(); print(mp.models.keys())"

# Testing de WiFi (requiere privilegios)
sudo python -c "from modules.wifi import proton_wifi_scan; print(proton_wifi_scan())"
```

### Logging y Debug

```python
# Configurar logging detallado
logging.basicConfig(level=logging.DEBUG)

# Logs específicos por módulo
logger = logging.getLogger(__name__)
logger.info("Información general")
logger.warning("Advertencia")
logger.error("Error crítico")
```

## 📊 Monitoreo y Métricas

### Health Checks

```bash
# Verificar estado de aplicación
curl http://localhost:8080/api/status

# Verificar modelos disponibles
curl http://localhost:8080/api/models

# Verificar conectividad WiFi
curl http://localhost:8080/api/wifi/status
```

### Métricas Clave

- **Predicciones por Hora**: Número de análisis realizados
- **Tasa de Éxito**: Porcentaje de predicciones exitosas
- **Modelos Activos**: Cantidad de modelos cargados
- **Conectividad**: Estado de conexión a PCH-Cloud y WiFi
- **Uso de Base de Datos**: Tamaño y número de registros

## 🐛 Troubleshooting

### Problemas Comunes

#### Error: "No wireless interface found"
```bash
# Verificar interfaces disponibles
docker exec -it container_name ip link show
docker exec -it container_name iwconfig

# Solución: Ejecutar con privilegios de red
docker run --privileged --network=host imagen
```

#### Error: "Model not found"
```bash
# Verificar modelos disponibles
docker exec -it container_name ls -la /app/models/

# Verificar carga de modelos
docker exec -it container_name python -c "from modules.model_predictor import ModelPredictor; print(ModelPredictor().models)"
```

#### Error: "Database locked"
```bash
# Verificar procesos usando la BD
docker exec -it container_name lsof /app/db/predictions.db

# Reiniciar aplicación
docker restart container_name
```

#### Error: "PCH-Cloud connection failed"
```bash
# Verificar configuración
docker exec -it container_name cat /app/config/config.json

# Verificar conectividad
docker exec -it container_name curl -I https://api.pch-cloud.com
```

### Logs Útiles

```bash
# Logs en tiempo real
docker logs -f container_name

# Logs filtrados
docker logs container_name 2>&1 | grep ERROR
docker logs container_name 2>&1 | grep WARNING

# Logs de módulos específicos
docker logs container_name 2>&1 | grep "model_predictor"
docker logs container_name 2>&1 | grep "wifi"
```

## 🔄 Despliegue en Producción

### Consideraciones de Seguridad

1. **Privilegios del Contenedor**: Minimizar usando capabilities específicas
2. **Red Host**: Evaluar alternativas más seguras para WiFi
3. **Credenciales**: Usar secrets management
4. **SSL/TLS**: Configurar certificados para HTTPS

### Optimizaciones de Performance

```bash
# Limitar recursos del contenedor
docker run --memory=1g --cpus=2 pch-monitoring

# Usar volúmenes para persistencia
docker run -v /host/db:/app/db -v /host/models:/app/models pch-monitoring
```

### Docker Compose Example

```yaml
version: '3.8'
services:
  pch-monitoring:
    build: .
    ports:
      - "8080:8080"
    network_mode: host
    privileged: true
    volumes:
      - ./data/db:/app/db
      - ./data/logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
```

## 📞 Soporte y Contribución

### Contacto
- **Equipo**: Proctek Team
- **Email**: [contact email]
- **Repositorio**: [GitHub URL]

### Contribuir

1. Fork el repositorio
2. Crear feature branch
3. Commit cambios
4. Crear Pull Request

### Roadmap

**v1.1**
- Autenticación de usuarios
- API REST completa
- Alertas por email/SMS

**v1.2**
- Soporte multi-tenant
- Dashboard administrativo
- Análisis histórico avanzado

---

**Versión**: 1.0.0  
**Fecha**: Julio 2025  
**Estado**: Producción  
**Licencia**: [Especificar licencia]
