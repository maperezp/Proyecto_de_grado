# Proyecto de Grado - Desarrollo de un algoritmo de machine
 learning en dispositivo IoT para
 aplicaci´ on industrial de an´ alisis de
 vibraciones

Sistema de monitoreo en tiempo real para dispositivos PCH-Cloud con análisis de machine learning, visualización de señales y gestión de conectividad WiFi.

## 📋 Descripción General

Esta aplicación Docker proporciona una plataforma completa de monitoreo para dispositivos IoT de vibración, integrando:

- **Análisis de Machine Learning**: Predicciones automáticas usando modelos Random Forest
- **Visualización de Señales**: Análisis en dominio de tiempo y frecuencia
- **Gestión WiFi**: Configuración y monitoreo de conectividad inalámbrica
- **Dashboard Web**: Interfaz interactiva para control y visualización
- **Base de Datos**: Almacenamiento persistente de predicciones e historial

## 🏗️ Arquitectura del Sistema

```
docker-ml-app-deploy/
├── dockerfile                 # Configuración del contenedor Docker
├── requirements.txt          # Dependencias Python
├── README.md                # Documentación principal
├── DEPLOY-SYMPHONY-BOARD.md # Guía de despliegue
└── src/                     # Código fuente de la aplicación
    ├── app.py              # Aplicación principal FastAPI
    ├── static/             # Archivos web estáticos
    │   ├── dashboard.html  # Dashboard principal
    │   ├── dashboard.js    # Lógica JavaScript
    │   ├── wifi-config.html # Configuración WiFi
    │   ├── wifi-config.js   # Lógica WiFi
    │   └── style.css       # Estilos CSS
    ├── modules/            # Módulos Python
    │   ├── pch_client.py   # Cliente PCH-Cloud
    │   ├── model_predictor.py # Motor de predicciones ML
    │   ├── plot_utils.py   # Generación de gráficos
    │   ├── prediction_db.py # Base de datos SQLite
    │   ├── wifi.py         # Gestión WiFi
    │   └── ...
    ├── models/             # Modelos ML pre-entrenados
    │   ├── myRF_3axis_50000.joblib
    │   ├── myRF_axial_50000.joblib
    │   ├── myRF_radial_50000.joblib
    │   └── myRF_tangential_50000.joblib
    └── db/                 # Base de datos local
        └── predictions.db
```

## 🚀 Características Principales

### 1. Dashboard de Monitoreo
- **Interfaz Web Responsiva**: Acceso desde cualquier dispositivo
- **Monitoreo en Tiempo Real**: Visualización de estado de dispositivos
- **Historial de Predicciones**: Tabla interactiva con resultados
- **Filtros por Período**: Análisis por hora, día, período personalizado

### 2. Análisis de Machine Learning
- **Modelos Random Forest**: 4 modelos especializados por eje y combinado
- **Clasificación Automática**: Detección de fallas de rodamientos y desbalances
- **Análisis por Canal**: Soporte para múltiples canales de sensores
- **Métricas de Confianza**: Probabilidades y niveles de certeza

### 3. Visualización de Señales
- **Dominio del Tiempo**: Gráficos de amplitud vs tiempo
- **Análisis FFT**: Espectro de frecuencias interactivo
- **Estadísticas**: RMS, pico, frecuencia de muestreo, duración
- **Plotly Integration**: Gráficos interactivos y responsivos

### 4. Gestión WiFi
- **Escaneo de Redes**: Detección automática de redes disponibles
- **Conexión Automática**: Soporte para redes abiertas y seguras
- **Estado en Tiempo Real**: Monitoreo de conectividad
- **Múltiples Métodos**: nmcli, wpa_supplicant, iwconfig

### 5. Base de Datos
- **SQLite Local**: Almacenamiento sin dependencias externas
- **Historial Completo**: Todas las predicciones y metadatos
- **Consultas Optimizadas**: Filtros por dispositivo, fecha, modelo
- **Gestión Automática**: Creación y mantenimiento de tablas

## 🛠️ Instalación y Despliegue

### Prerrequisitos
- Docker instalado
- Puerto 8080 disponible
- Privilegios de red para gestión WiFi
- Python

### Construcción del Contenedor

```bash
# Clonar el repositorio
git clone [repository-url]
cd docker-ml-app-deploy

# Construir la imagen Docker
docker build -t pch-monitoring .

# Ejecutar el contenedor
docker run -d \
  --name pch-app \
  --network=host \
  --privileged \
  -p 8080:8080 \
  pch-monitoring
```

### Configuración de Red
Para la gestión WiFi, el contenedor requiere:
- `--network=host`: Acceso a interfaces de red del host
- `--privileged`: Permisos para configuración de red

### Acceso a la Aplicación
- **Dashboard Principal**: `http://localhost:8080`
- **Configuración WiFi**: `http://localhost:8080/wifi`
- **API Documentation**: `http://localhost:8080/docs`

## 📡 API Endpoints

### Sistema
- `GET /api/status` - Estado general de la aplicación
- `GET /api/models` - Modelos ML disponibles

### Dispositivos
- `GET /api/devices` - Lista de dispositivos conectados
- `GET /api/devices/{device_id}` - Información específica

### Grabaciones
- `POST /api/recordings/{device_id}/period` - Datos por período
- `GET /api/recordings/{device_id}/{recording_id}/samples` - Muestras

### Predicciones
- `POST /api/predict/period` - Predicciones por período
- `GET /api/predictions/recent` - Predicciones recientes
- `DELETE /api/predictions/{prediction_id}` - Eliminar predicción

### Análisis de Señales
- `POST /api/signal/period/{device_id}` - Análisis de señal

### WiFi
- `POST /api/wifi/connect` - Conectar a red
- `GET /api/wifi/status` - Estado de conexión
- `GET /api/wifi/scan` - Escanear redes

## 🤖 Modelos de Machine Learning

### Tipos de Modelos
1. **myRF_3axis_50000**: Análisis combinado de 3 ejes
2. **myRF_axial_50000**: Análisis eje axial
3. **myRF_radial_50000**: Análisis eje radial
4. **myRF_tangential_50000**: Análisis eje tangencial

### Clases de Predicción
- `normal`: Funcionamiento normal
- `horizontal-misalignment`: Desalineación horizontal
- `vertical-misalignment`: Desalineación vertical
- `imbalance`: Desbalance
- `ball_fault`: Falla en bolas de rodamiento
- `cage_fault`: Falla en jaula de rodamiento
- `outer_race`: Falla en pista externa

### Características Extraídas
- **Dominio del Tiempo**: RMS, pico, curtosis, asimetría
- **Dominio de Frecuencia**: Frecuencia dominante, energía espectral, centroide

## 🔧 Configuración

### Variables de Entorno
```bash
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
```

### Configuración PCH-Cloud
Crear archivos en `/app/config/`:
- `config.json`: Credenciales de usuario
- `hosts.json`: Configuración de servidores

### Puertos y Servicios
- **Aplicación Web**: Puerto 8080
- **Base de Datos**: SQLite local
- **Logs**: stdout/stderr

## 📊 Monitoreo y Logging

### Niveles de Log
- `INFO`: Operaciones normales
- `WARNING`: Advertencias y fallbacks
- `ERROR`: Errores críticos

### Métricas Disponibles
- Conexiones a PCH-Cloud
- Predicciones realizadas
- Estado de modelos ML
- Conectividad WiFi
- Uso de base de datos

## 🔒 Seguridad

### Consideraciones
- **Privilegios de Contenedor**: Requeridos para gestión WiFi
- **Red del Host**: Acceso necesario para interfaces WiFi
- **Credenciales**: Almacenadas en archivos de configuración

### Recomendaciones
- Cambiar credenciales por defecto
- Limitar acceso de red
- Monitorear logs de seguridad

## 🐛 Troubleshooting

### Problemas Comunes

**Error de conexión WiFi**
```bash
# Verificar privilegios del contenedor
docker run --privileged --network=host pch-monitoring

# Verificar interfaces disponibles
docker exec -it pch-app iwconfig
```

**Modelos ML no cargan**
```bash
# Verificar archivos de modelo
docker exec -it pch-app ls -la /app/models/

# Verificar logs
docker logs pch-app
```

**Base de datos no inicializa**
```bash
# Verificar permisos de directorio
docker exec -it pch-app ls -la /app/db/

# Recrear base de datos
docker exec -it pch-app rm /app/db/predictions.db
docker restart pch-app
```

## 📈 Performance

### Optimizaciones Implementadas
- **Cache de Dispositivos**: Reduce llamadas a API
- **Consultas Eficientes**: Índices en base de datos
- **Gráficos Lazy**: Carga bajo demanda
- **Procesamiento Batch**: Múltiples predicciones

### Límites Recomendados
- **Predicciones Simultáneas**: 50 recordings máximo
- **Historial de Base de Datos**: 10,000 predicciones
- **Tamaño de Señal**: 50,000 muestras por análisis

## 🔄 Actualizaciones y Mantenimiento

### Actualización de Modelos
```bash
# Copiar nuevos modelos
docker cp new_model.joblib pch-app:/app/models/

# Reiniciar aplicación
docker restart pch-app
```

### Backup de Base de Datos
```bash
# Crear backup
docker cp pch-app:/app/db/predictions.db ./backup_$(date +%Y%m%d).db

# Restaurar backup
docker cp backup_20250728.db pch-app:/app/db/predictions.db
```

## 📞 Soporte

### Contacto
- **Equipo**: Proctek Team
- **Versión**: 1.0.0
- **Repositorio**: [GitHub Repository]

### Logs Útiles
```bash
# Logs en tiempo real
docker logs -f pch-app

# Logs específicos
docker exec -it pch-app tail -f /app/logs/app.log
```

---

## 🏷️ Tags y Versiones

- **Tecnologías**: FastAPI, Docker, SQLite, Plotly, scikit-learn
- **Compatibilidad**: ARM64/AMD64
- **Última Actualización**: Julio 2025
- **Estado**: Producción

Esta documentación cubre todos los aspectos técnicos y operativos de la aplicación Docker desarrollada para el monitoreo en tiempo real de dispositivos PCH-Cloud.

