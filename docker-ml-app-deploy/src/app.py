"""
PCH-Cloud Real-Time Monitoring Application

This FastAPI application provides real-time monitoring capabilities for PCH-Cloud devices,
including machine learning predictions, signal analysis, and WiFi configuration management.

Main Features:
- Device monitoring and data collection from PCH-Cloud
- Real-time ML predictions on vibration data
- Signal visualization (time domain and FFT)
- Database storage for predictions history
- WiFi network configuration and management
- Web dashboard for monitoring and control

Author: Proctek Team
Version: 1.0.0
"""

import json
import uvicorn
import os
from datetime import datetime
from typing import Optional, AsyncGenerator, List, Dict, Any
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel, Field

# Importar módulos personalizados
from modules.pch_client import PCHCloudClient
from modules.model_predictor import ModelPredictor
from modules.plot_utils import PlotGenerator
from modules.prediction_db import PredictionDatabase
from modules import wifi



# ============================================================================
# PYDANTIC MODELS FOR API DOCUMENTATION
# ============================================================================

class WiFiConfig(BaseModel):
    """ Model for Wifi Config"""
    ssid: str
    password: str

class PeriodRequest(BaseModel):
    """Model for period-based requests"""
    period_type: str = Field(..., description="Type of period: 'last_minute', 'last_hour', 'last_24h', 'custom'")
    hours_back: Optional[int] = Field(None, description="Hours to look back (for non-custom periods)")
    start_time: Optional[str] = Field(None, description="Start time for custom period (ISO format)")
    end_time: Optional[str] = Field(None, description="End time for custom period (ISO format)")

class PredictionRequest(BaseModel):
    """Model for prediction requests"""
    device_id: str = Field(..., description="ID of the device to analyze")
    model_name: str = Field(default="myRF_3axis_50000", description="Name of the ML model to use")
    period: PeriodRequest = Field(..., description="Time period for predictions")
    channel: int = Field(default=1, description="Channel number to analyze")

class SignalRequest(BaseModel):
    """Model for signal analysis requests"""
    period: PeriodRequest = Field(..., description="Time period for signal analysis")
    channel: int = Field(default=1, description="Channel number to analyze")

class StatusResponse(BaseModel):
    """Model for application status response"""
    application: str
    version: str
    status: str
    pch_cloud: Dict[str, Any]
    models: Dict[str, Any]
    database: Dict[str, Any]
    timestamp: str

class PredictionResponse(BaseModel):
    """Model for prediction responses"""
    device_id: str
    period: Dict[str, Any]
    model_used: str
    predictions: List[Dict[str, Any]]
    summary: Dict[str, Any]

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# APPLICATION LIFESPAN MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan event handler for FastAPI application.
    
    Manages startup and shutdown processes including:
    - PCH-Cloud connection initialization
    - Application startup logging
    - Resource cleanup on shutdown
    """
    # Startup
    logger.info("Starting PCH-Cloud monitoring application...")
    logger.info("Dashboard will be available at:")
    logger.info("  - http://localhost:8000")
    logger.info("  - http://127.0.0.1:8000")
    logger.info("  - http://0.0.0.0:8000 (if accessing from other devices)")
    
    # Intentar login a PCH-Cloud
    try:
        login_success = await pch_client.login()
        if login_success:
            logger.info("✓ Successfully connected to PCH-Cloud")
        else:
            logger.warning("⚠ Could not connect to PCH-Cloud - check credentials")
    except Exception as e:
        logger.error(f"✗ PCH-Cloud connection error: {e}")
        logger.info("Application will start in demo mode")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PCH-Cloud monitoring application...")

# ============================================================================
# FASTAPI APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title="PCH-Cloud Real-Time Monitoring", 
    version="1.0.0",
    description="""
    Real-time monitoring application for PCH-Cloud devices with ML predictions.
    
    ## Features
    
    * **Device Monitoring**: Real-time data collection from PCH-Cloud devices
    * **ML Predictions**: Machine learning analysis of vibration data
    * **Signal Analysis**: Time domain and frequency domain visualization
    * **Database Storage**: Persistent storage of predictions and results
    * **WiFi Management**: Network configuration and status monitoring
    * **Web Dashboard**: Interactive monitoring interface
    
    ## API Sections
    
    * **Frontend**: Web pages and static content
    * **System**: Application status and configuration
    * **Devices**: Device management and information
    * **Recordings**: Data collection and retrieval
    * **Predictions**: ML analysis and results
    * **Signal Analysis**: Data visualization and processing
    * **WiFi**: Network configuration management
    """,
    lifespan=lifespan,
    tags_metadata=[
        {"name": "frontend", "description": "Web interface endpoints"},
        {"name": "system", "description": "Application status and configuration"},
        {"name": "devices", "description": "Device management"},
        {"name": "recordings", "description": "Data collection and retrieval"},
        {"name": "predictions", "description": "Machine learning predictions"},
        {"name": "signal", "description": "Signal analysis and visualization"},
        {"name": "wifi", "description": "WiFi network management"},
    ]
)

# ============================================================================
# STATIC FILES AND TEMPLATES CONFIGURATION
# ============================================================================

# Obtener el directorio donde está este archivo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_DIR = os.path.join(BASE_DIR, "db")

# Crear directorio de base de datos si no existe
os.makedirs(DB_DIR, exist_ok=True)

templates = Jinja2Templates(directory=STATIC_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ============================================================================
# GLOBAL INSTANCES AND CONFIGURATION
# ============================================================================

# Instancias globales con path absoluto para la base de datos
pch_client = PCHCloudClient()
model_predictor = ModelPredictor()
plot_generator = PlotGenerator()
prediction_db = PredictionDatabase(db_path=os.path.join(DB_DIR, "predictions.db"))

# Cache para nombres de dispositivos
device_names_cache = {}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def get_device_name(device_id: str) -> str:
    """
    Obtener el nombre del dispositivo desde la cache o desde la API.
    
    Args:
        device_id: ID único del dispositivo
        
    Returns:
        str: Nombre del dispositivo o el ID si no se puede obtener el nombre
        
    Note:
        Utiliza un cache global para evitar consultas repetitivas a la API
    """
    global device_names_cache
    
    # Si ya está en cache, devolverlo
    if device_id in device_names_cache:
        return device_names_cache[device_id]
    
    try:
        # Obtener todos los dispositivos y actualizar cache
        devices = await pch_client.get_devices()
        for device in devices:
            device_names_cache[device.get("id", "")] = device.get("name", device.get("id", "Unknown"))
        
        # Devolver el nombre del dispositivo solicitado
        return device_names_cache.get(device_id, device_id)
    
    except Exception as e:
        logger.error(f"Error getting device name for {device_id}: {e}")
        return device_id  # Fallback al ID si no se puede obtener el nombre

# ============================================================================
# FRONTEND ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse, tags=["frontend"])
async def dashboard(request: Request):
    """
    Página principal del dashboard de monitoreo.
    
    Proporciona la interfaz web principal para:
    - Visualización de dispositivos conectados
    - Monitoreo en tiempo real
    - Historial de predicciones
    - Controles de análisis
    
    Returns:
        HTMLResponse: Página HTML del dashboard principal
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/wifi", response_class=HTMLResponse, tags=["frontend"])
async def wifi_config(request: Request):
    """
    Página de configuración WiFi.
    
    Proporciona interfaz web para:
    - Escaneo de redes WiFi disponibles
    - Configuración de conexiones
    - Estado de conectividad
    - Gestión de redes guardadas
    
    Returns:
        HTMLResponse: Página HTML de configuración WiFi
    """
    return templates.TemplateResponse("wifi-config.html", {"request": request})

# ============================================================================
# SYSTEM STATUS ENDPOINTS
# ============================================================================


@app.get("/api/status", response_model=StatusResponse, tags=["system"])
async def get_status():
    """
    Obtener el estado general de la aplicación.
    
    Proporciona información completa sobre:
    - Estado de conexión con PCH-Cloud
    - Modelos ML cargados y disponibles
    - Estadísticas de la base de datos
    - Información de la aplicación
    
    Returns:
        StatusResponse: Estado completo del sistema
        
    Example:
        ```json
        {
            "application": "PCH-Cloud Real-Time Monitoring",
            "version": "1.0.0",
            "status": "running",
            "pch_cloud": {
                "connected": true,
                "host": "api.pch-cloud.com",
                "username": "user@example.com"
            },
            "models": {
                "loaded": 4,
                "available": ["myRF_3axis_50000", "myRF_axial_50000", ...]
            },
            "database": {
                "total_predictions": 1234,
                "file_size_mb": 5.2,
                "oldest_record": "2025-01-01T00:00:00",
                "newest_record": "2025-07-21T12:00:00"
            }
        }
        ```
    """
    # Obtener información de la base de datos
    db_info = prediction_db.get_database_info()
    
    return {
        "application": "PCH-Cloud Real-Time Monitoring",
        "version": "1.0.0",
        "status": "running",
        "pch_cloud": {
            "connected": pch_client.token is not None,
            "host": pch_client.config.get("host", "unknown"),
            "username": pch_client.config.get("username", "unknown")
        },
        "models": {
            "loaded": len(model_predictor.models),
            "available": list(model_predictor.models.keys())[:5]  # Primeros 5
        },
        "database": {
            "total_predictions": db_info.get("total_records", 0),
            "file_size_mb": db_info.get("file_size_mb", 0),
            "oldest_record": db_info.get("oldest_record"),
            "newest_record": db_info.get("newest_record")
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/models", tags=["system"])
async def get_available_models():
    """
    Obtener lista de modelos ML disponibles.
    
    Returns:
        dict: Lista de modelos cargados y disponibles para predicciones
        
    Example:
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
    """
    return {"models": list(model_predictor.models.keys())}

# ============================================================================
# DEVICE MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/devices", tags=["devices"])
async def get_devices():
    """
    Obtener lista de dispositivos conectados.
    
    Recupera todos los dispositivos disponibles desde PCH-Cloud
    o proporciona datos de demostración si no hay conexión.
    
    Returns:
        dict: Lista de dispositivos con información básica
        
    Example:
        ```json
        {
            "devices": [
                {
                    "id": "device_001",
                    "name": "CT Fan 1",
                    "status": "online",
                    "last_seen": "2025-07-21T12:00:00Z"
                }
            ],
            "count": 1,
            "connected": true
        }
        ```
    """
    try:
        devices = await pch_client.get_devices()
        return {
            "devices": devices,
            "count": len(devices),
            "connected": pch_client.token is not None
        }
    except Exception as e:
        logger.error(f"Error in get_devices endpoint: {e}")
        # Devolver dispositivos de demo si hay error
        demo_devices = DemoDataProvider.get_demo_devices()
        return {
            "devices": demo_devices,
            "count": len(demo_devices),
            "connected": False,
            "demo_mode": True
        }


@app.get("/api/channels/{device_id}", tags=["devices"])
async def get_device_channels(
    device_id: str = Path(..., description="ID único del dispositivo")
):
    """
    Obtener información de canales disponibles de un dispositivo.
    
    Args:
        device_id: ID único del dispositivo
        
    Returns:
        dict: Información de canales disponibles
        
    Example:
        ```json
        {
            "channels": [1, 2, 3, 4],
            "max_channels": 4,
            "default_channel": 1,
            "recording_info": {
                "recording_id": "rec_123",
                "total_recordings": 45
            }
        }
        ```
    """
    try:
        # Obtener una grabación reciente para determinar los canales disponibles
        recordings = await pch_client.get_recordings(device_id, 1)  # Última hora
        
        if not recordings:
            # Si no hay grabaciones recientes, asumir 1 canal por defecto
            return {
                "channels": [1],
                "max_channels": 1,
                "default_channel": 1,
                "message": "No recent recordings found, showing default channels"
            }
        
        # Tomar la primera grabación para obtener el número de canales
        first_recording = recordings[0]
        numberOfChannels = first_recording.get('numberOfChannels', 1)
        
        channels = list(range(1, numberOfChannels + 1))
        
        return {
            "channels": channels,
            "max_channels": numberOfChannels,
            "default_channel": 1,
            "recording_info": {
                "recording_id": first_recording.get('id'),
                "total_recordings": len(recordings)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting device channels: {e}")
        # En caso de error, devolver configuración por defecto
        return {
            "channels": [1],
            "max_channels": 1,
            "default_channel": 1,
            "error": str(e)
        }

# ============================================================================
# RECORDINGS AND DATA COLLECTION ENDPOINTS
# ============================================================================


@app.post("/api/recordings/{device_id}/period", tags=["recordings"])
async def get_recordings_by_period(
    device_id: str,
    period_data: dict
):
    """
    Obtener grabaciones de un dispositivo en un período específico.
    
    Args:
        device_id: ID único del dispositivo
        period_data: Configuración del período incluyendo tipo y fechas
        
    Returns:
        dict: Grabaciones encontradas en el período especificado
        
    Example Request:
        ```json
        {
            "period_type": "last_24h",
            "hours_back": 24
        }
        ```
        
    Example Response:
        ```json
        {
            "recordings": [
                {
                    "id": "rec_123",
                    "timestamp": "2025-07-21T12:00:00Z",
                    "numberOfChannels": 4,
                    "duration": 10.0
                }
            ],
            "count": 1,
            "period_type": "last_24h",
            "period_info": {...}
        }
        ```
    """
    period_type = period_data.get("period_type", "hours")
    
    # Calcular horas basado en el tipo de período
    if period_type == "last_minute":
        hours_back = 1/60  # 1 minuto en horas
    elif period_type == "last_hour":
        hours_back = 1
    elif period_type == "last_24h":
        hours_back = 24
    elif period_type == "custom":
        hours_back = _calculate_custom_period_hours(period_data)
    else:
        hours_back = int(period_data.get("hours_back", 24))
    
    recordings = await pch_client.get_recordings(device_id, int(max(hours_back, 0.016)))  # Mínimo 1 minuto
    
    # Filtrar por fechas específicas si es período personalizado
    if period_type == "custom" and period_data.get("start_time") and period_data.get("end_time"):
        recordings = _filter_recordings_by_custom_dates(recordings, period_data)
    
    return {
        "recordings": recordings,
        "count": len(recordings),
        "period_type": period_type,
        "period_info": period_data
    }

@app.get("/api/plot/{device_id}/{recording_id}", tags=["recordings"])
async def get_plot_data(
    device_id: str = Path(..., description="ID único del dispositivo"),
    recording_id: str = Path(..., description="ID único de la grabación"),
    channel: int = Query(default=1, description="Número de canal a analizar")
):
    """
    Generar datos de gráfico para una grabación específica.
    
    Args:
        device_id: ID único del dispositivo
        recording_id: ID único de la grabación
        channel: Número de canal a analizar (default: 1)
        
    Returns:
        dict: Datos de gráficos, predicción y estadísticas
        
    Example:
        ```json
        {
            "time_plot": {...},
            "fft_plot": {...},
            "prediction": {
                "prediction": "Normal",
                "probabilities": {"Normal": 0.95, "Faulty": 0.05}
            },
            "stats": {
                "rms": 0.123,
                "peak": 0.456,
                "mean": 0.001
            }
        }
        ```
    """
    try:
        data = await pch_client.get_recording_data(device_id, recording_id, channel)
        
        if "samples" in data:
            samples = data["samples"]
            delta = data.get("delta", 1/25000)  # Tiempo entre muestras
            
            # Generar gráficos usando PlotGenerator
            time_plot = plot_generator.generate_time_plot(samples, delta, device_id)
            fft_plot = plot_generator.generate_fft_plot(samples, delta, device_id)
            stats = plot_generator.calculate_stats(samples, delta)
            
            # Realizar predicción
            prediction = model_predictor.predict(data)
            
            return {
                "time_plot": time_plot,
                "fft_plot": fft_plot,
                "prediction": prediction,
                "stats": stats
            }
        
        return {"error": "No samples data found"}
        
    except Exception as e:
        logger.error(f"Error generating plot data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PREDICTION ENDPOINTS
# ============================================================================

def _calculate_custom_period_hours(period_data):
    """
    Calcular horas para período personalizado.
    
    Args:
        period_data: Diccionario con start_time y end_time
        
    Returns:
        float: Número de horas en el período
    """
    start_time = period_data.get("start_time")
    end_time = period_data.get("end_time")
    if start_time and end_time:
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        return (end_dt - start_dt).total_seconds() / 3600
    return 24  # Default fallback


def _filter_recordings_by_custom_dates(recordings, period_data):
    """
    Filtrar grabaciones por fechas personalizadas.
    
    Args:
        recordings: Lista de grabaciones
        period_data: Configuración del período con fechas
        
    Returns:
        list: Grabaciones filtradas por fechas
    """
    from datetime import datetime
    start_dt = datetime.fromisoformat(period_data["start_time"].replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(period_data["end_time"].replace('Z', '+00:00'))
    
    filtered_recordings = []
    for recording in recordings:
        recording_time = recording.get("timestamp") or recording.get("created")
        if recording_time:
            recording_dt = datetime.fromisoformat(recording_time.replace('Z', '+00:00'))
            if start_dt <= recording_dt <= end_dt:
                filtered_recordings.append(recording)
    return filtered_recordings


@app.post("/api/predict/period", tags=["predictions"])
async def predict_period_data(request_data: dict):
    """
    Realizar predicciones ML sobre un período de tiempo específico.
    
    Analiza múltiples grabaciones de un dispositivo en un período determinado
    usando modelos de machine learning para clasificar el estado del equipo.
    
    Args:
        request_data: Configuración de la predicción incluyendo dispositivo, modelo y período
        
    Returns:
        PredictionResponse: Resultados de predicciones y estadísticas del período
        
    Example Request:
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
        
    Example Response:
        ```json
        {
            "device_id": "device_001",
            "model_used": "myRF_3axis_50000",
            "predictions": [
                {
                    "recording_id": "rec_123",
                    "timestamp": "2025-07-21T12:00:00Z",
                    "prediction": {
                        "prediction": "Normal",
                        "probabilities": {"Normal": 0.95, "Faulty": 0.05}
                    },
                    "success": true
                }
            ],
            "summary": {
                "total_recordings": 10,
                "successful_predictions": 9,
                "failed_predictions": 1,
                "most_common_prediction": {
                    "class": "Normal",
                    "percentage": 89
                }
            }
        }
        ```
    """
    device_id = request_data.get("device_id")
    model_name = request_data.get("model_name", "myRF_3axis_50000")
    period_data = request_data.get("period", {})
    channel = request_data.get("channel", 1)
    
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id is required")
    
    try:
        # Obtener recordings del período especificado
        period_response = await get_recordings_by_period(device_id, period_data)
        recordings = period_response["recordings"]
        
        if not recordings:
            return {
                "error": "No recordings found for the specified period",
                "predictions": [],
                "summary": {
                    "total_recordings": 0,
                    "successful_predictions": 0,
                    "failed_predictions": 0
                }
            }
        
        predictions = []
        successful_count = 0
        failed_count = 0
        
        # Obtener el nombre del dispositivo una vez
        device_name = await get_device_name(device_id)
        
        # Realizar predicciones para cada recording
        for recording in recordings:
            recording_id = recording.get("id")
            if recording_id:
                recording_timestamp = recording.get("timestamp", recording.get("created"))
                try:
                    # Obtener datos del recording
                    data = await pch_client.get_recording_data(device_id, recording_id, channel)
                    
                    # Realizar predicción
                    prediction = model_predictor.predict(data, model_name)
                    
                    # Guardar en base de datos con nombre del dispositivo
                    prediction_db.save_prediction(
                        device_id=device_id,
                        recording_id=recording_id,
                        model_name=model_name,
                        channel=channel,
                        prediction_result=prediction,
                        success=True,
                        timestamp=recording_timestamp,
                        device_name=device_name
                    )
                    
                    predictions.append({
                        "recording_id": recording_id,
                        "timestamp": recording_timestamp,
                        "prediction": prediction,
                        "success": True
                    })
                    successful_count += 1
                    
                except Exception as e:
                    error_message = str(e)
                    
                    # Guardar error en base de datos con nombre del dispositivo
                    prediction_db.save_prediction(
                        device_id=device_id,
                        recording_id=recording_id,
                        model_name=model_name,
                        channel=channel,
                        prediction_result=None,
                        success=False,
                        timestamp=recording_timestamp,
                        error_message=error_message,
                        device_name=device_name
                    )
                    
                    predictions.append({
                        "recording_id": recording_id,
                        "timestamp": recording_timestamp,
                        "error": error_message,
                        "success": False
                    })
                    failed_count += 1
        
        # Calcular estadísticas del período
        summary_stats = _calculate_period_summary(predictions)
        
        return {
            "device_id": device_id,
            "period": period_data,
            "model_used": model_name,
            "predictions": predictions,
            "summary": {
                "total_recordings": len(recordings),
                "successful_predictions": successful_count,
                "failed_predictions": failed_count,
                **summary_stats
            }
        }
        
    except Exception as e:
        logger.error(f"Error in predict_period_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _calculate_period_summary(predictions):
    """
    Calcular estadísticas resumidas de las predicciones del período.
    
    Args:
        predictions: Lista de predicciones realizadas
        
    Returns:
        dict: Estadísticas y distribución de predicciones
    """
    successful_predictions = [p for p in predictions if p.get("success")]
    
    if not successful_predictions:
        return {"prediction_distribution": {}}
    
    # Contar distribución de predicciones
    prediction_counts = {}
    total_predictions = len(successful_predictions)
    
    for pred in successful_predictions:
        prediction_result = pred.get("prediction", {})
        if isinstance(prediction_result, dict):
            prediction_class = prediction_result.get("prediction", "unknown")
        else:
            prediction_class = str(prediction_result)
            
        prediction_counts[prediction_class] = prediction_counts.get(prediction_class, 0) + 1
    
    # Calcular porcentajes
    prediction_distribution = {
        class_name: {
            "count": count,
            "percentage": round((count / total_predictions) * 100, 2)
        }
        for class_name, count in prediction_counts.items()
    }
    
    # Encontrar predicción más común
    most_common = max(prediction_counts.items(), key=lambda x: x[1]) if prediction_counts else ("unknown", 0)
    
    return {
        "prediction_distribution": prediction_distribution,
        "most_common_prediction": {
            "class": most_common[0],
            "count": most_common[1],
            "percentage": round((most_common[1] / total_predictions) * 100, 2) if total_predictions > 0 else 0
        }
    }

@app.delete("/api/predictions/{prediction_id}", tags=["predictions"])
async def delete_prediction(
    prediction_id: int = Path(..., description="ID único de la predicción a eliminar")
):
    """
    Eliminar una predicción específica de la base de datos.
    
    Args:
        prediction_id: ID único de la predicción
        
    Returns:
        dict: Confirmación de eliminación
        
    Raises:
        HTTPException: 404 si la predicción no existe, 500 para errores del servidor
    """
    try:
        deleted = prediction_db.delete_prediction(prediction_id)
        if deleted:
            return {"message": "Prediction deleted successfully", "id": prediction_id}
        else:
            raise HTTPException(status_code=404, detail="Prediction not found")
    except Exception as e:
        logger.error(f"Error deleting prediction {prediction_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/predictions/recent", tags=["predictions"])
async def get_recent_predictions(
    device_id: Optional[str] = Query(None, description="ID del dispositivo para filtrar (opcional)"),
    limit: int = Query(default=50, ge=1, le=1000, description="Número máximo de predicciones a retornar")
):
    """
    Obtener las predicciones más recientes de la base de datos.
    
    Args:
        device_id: ID del dispositivo para filtrar (opcional)
        limit: Número máximo de predicciones a retornar (1-1000)
        
    Returns:
        dict: Lista de predicciones recientes con metadatos
        
    Example:
        ```json
        {
            "predictions": [
                {
                    "id": 123,
                    "device_id": "device_001",
                    "recording_id": "rec_456",
                    "timestamp": "2025-07-21T12:00:00Z",
                    "prediction": {
                        "prediction": "Normal",
                        "probabilities": {"Normal": 0.95, "Faulty": 0.05}
                    },
                    "success": true,
                    "model_name": "myRF_3axis_25000",
                    "confidence": 0.95
                }
            ],
            "count": 1,
            "device_id": "device_001"
        }
        ```
    """
    try:
        predictions = prediction_db.get_predictions(
            device_id=device_id,
            limit=limit
        )
        
        # Formatear para que sea compatible con el frontend
        formatted_predictions = []
        for pred in predictions:
            formatted_predictions.append({
                "id": pred["id"],  # Agregar ID para permitir eliminación
                "device_id": pred["device_id"],  # Incluir device_id
                "recording_id": pred["recording_id"],
                "timestamp": pred["timestamp"],
                "prediction": {
                    "prediction": pred["predicted_class"],
                    "probabilities": pred["probabilities"]
                },
                "success": pred["success"],
                "model_name": pred["model_name"],
                "channel": pred["channel"],
                "confidence": pred["confidence"],
                "created_at": pred["created_at"]
            })
        
        return {
            "predictions": formatted_predictions,
            "count": len(formatted_predictions),
            "device_id": device_id
        }
    except Exception as e:
        logger.error(f"Error getting recent predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/predictions/all", tags=["predictions"])
async def get_all_predictions():
    """
    Obtener TODAS las predicciones recientes de todos los dispositivos.
    
    Recupera las predicciones más recientes sin filtrar por dispositivo específico,
    útil para el dashboard principal y análisis global.
    
    Returns:
        dict: Lista completa de predicciones de todos los dispositivos
        
    Example:
        ```json
        {
            "predictions": [
                {
                    "id": 123,
                    "device_id": "device_001",
                    "device_name": "CT Fan 1",
                    "recording_id": "rec_456",
                    "timestamp": "2025-07-21T12:00:00Z",
                    "prediction": {
                        "prediction": "Normal",
                        "probabilities": {"Normal": 0.95, "Faulty": 0.05}
                    },
                    "success": true,
                    "model_name": "myRF_3axis_25000",
                    "confidence": 0.95
                }
            ],
            "count": 1,
            "message": "Showing 1 most recent predictions from all devices"
        }
        ```
    """
    try:
        # Obtener todas las predicciones recientes sin filtro de device_id
        predictions = prediction_db.get_predictions(
            device_id=None,  # Sin filtro de dispositivo
            limit=1000  # Límite razonable para evitar problemas de rendimiento
        )
        
        # Formatear para que sea compatible con el frontend
        formatted_predictions = []
        for pred in predictions:
            formatted_predictions.append({
                "id": pred["id"],  # Agregar ID para permitir eliminación
                "device_id": pred["device_id"],  # Incluir device_id
                "device_name": pred.get("device_name", pred["device_id"]),  # Incluir device_name
                "recording_id": pred["recording_id"],
                "timestamp": pred["timestamp"],
                "prediction": {
                    "prediction": pred["predicted_class"],
                    "probabilities": pred["probabilities"]
                },
                "success": pred["success"],
                "model_name": pred["model_name"],
                "channel": pred["channel"],
                "confidence": pred["confidence"],
                "created_at": pred["created_at"]
            })
        
        return {
            "predictions": formatted_predictions,
            "count": len(formatted_predictions),
            "message": f"Showing {len(formatted_predictions)} most recent predictions from all devices"
        }
    except Exception as e:
        logger.error(f"Error getting all predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SIGNAL ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/signal/period/{device_id}", tags=["signal"])
async def get_signal_data_for_period(
    device_id: str,
    request_data: dict
):
    """
    Obtener datos de señal agregados de un período de tiempo.
    
    Combina múltiples grabaciones de un período específico para generar
    visualizaciones de señal en dominio del tiempo y frecuencia.
    
    Args:
        device_id: ID único del dispositivo
        request_data: Configuración del período y canal
        
    Returns:
        dict: Gráficos de señal, estadísticas y información de muestreo
        
    Example Request:
        ```json
        {
            "period": {
                "period_type": "last_hour",
                "hours_back": 1
            },
            "channel": 1
        }
        ```
        
    Example Response:
        ```json
        {
            "time_plot": {...},
            "fft_plot": {...},
            "stats": {
                "rms": 0.123,
                "peak": 0.456,
                "mean": 0.001,
                "std": 0.234
            },
            "recordings_used": 3,
            "total_samples": 150000,
            "channel": 1,
            "sampling_info": {
                "delta": 4e-05,
                "frequency": 25000
            }
        }
        ```
    """
    period_data = request_data.get("period", {})
    channel = request_data.get("channel", 1)
    
    try:
        # Obtener recordings del período especificado
        period_response = await get_recordings_by_period(device_id, period_data)
        recordings = period_response["recordings"]
        
        if not recordings:
            return _create_empty_signal_response("No recordings found for the specified period")
        
        # Procesar grabaciones y obtener muestras
        signal_data = await _process_recordings_for_signal(device_id, recordings, channel)
        
        if not signal_data["samples"]:
            return _create_empty_signal_response(
                f"No valid sample data found in the recordings. Checked {signal_data['checked']} recordings.",
                signal_data
            )
        
        # Generar gráficos usando PlotGenerator
        time_plot = plot_generator.generate_time_plot(signal_data["samples"], signal_data["avg_delta"], f"{device_id}_period")
        fft_plot = plot_generator.generate_fft_plot(signal_data["samples"], signal_data["avg_delta"], f"{device_id}_period")
        stats = plot_generator.calculate_stats(signal_data["samples"], signal_data["avg_delta"])
        
        return {
            "time_plot": time_plot,
            "fft_plot": fft_plot,
            "stats": stats,
            "recordings_used": signal_data["valid"],
            "total_samples": len(signal_data["samples"]),
            "channel": channel,
            "sampling_info": {
                "delta": signal_data["avg_delta"],
                "frequency": 1/signal_data["avg_delta"] if signal_data["avg_delta"] > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_signal_data_for_period: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _process_recordings_for_signal(device_id: str, recordings: list, channel: int):
    """
    Procesar grabaciones para extraer datos de señal.
    
    Args:
        device_id: ID del dispositivo
        recordings: Lista de grabaciones a procesar
        channel: Número de canal a analizar
        
    Returns:
        dict: Datos de señal procesados con estadísticas
    """
    max_recordings = min(5, len(recordings))  # Máximo 5 para evitar sobrecarga
    selected_recordings = recordings[:max_recordings]
    
    all_samples = []
    deltas = []
    valid_recordings = 0
    
    for recording in selected_recordings:
        recording_id = recording.get("id")
        if not recording_id:
            continue
            
        try:
            # Verificar canales disponibles y ajustar si es necesario
            numberOfChannels = recording.get('numberOfChannels', 1)
            actual_channel = min(channel, numberOfChannels)
            
            if actual_channel != channel:
                logger.warning(f"Requested channel {channel} not available, using channel {actual_channel}")
            
            # Obtener datos del recording
            data = await pch_client.get_recording_data(device_id, recording_id, actual_channel)
            
            if "samples" in data and data["samples"]:
                all_samples.extend(data["samples"])
                deltas.append(data.get("delta", 1/25000))
                valid_recordings += 1
                logger.info(f"Added {len(data['samples'])} samples from recording {recording_id}, channel {actual_channel}")
                
        except Exception as e:
            logger.warning(f"Could not load recording {recording_id}: {e}")
            continue
    
    return {
        "samples": all_samples,
        "avg_delta": sum(deltas) / len(deltas) if deltas else 1/25000,
        "valid": valid_recordings,
        "checked": len(selected_recordings),
        "total": len(recordings)
    }


def _create_empty_signal_response(error_message: str, signal_data: Optional[dict] = None):
    """
    Crear respuesta vacía para señales cuando no hay datos.
    
    Args:
        error_message: Mensaje de error descriptivo
        signal_data: Datos opcionales para debugging
        
    Returns:
        dict: Respuesta estándar para casos sin datos
    """
    response = {
        "error": error_message,
        "time_plot": None,
        "fft_plot": None,
        "stats": None
    }
    
    if signal_data:
        response["debug_info"] = {
            "total_recordings": signal_data.get("total", 0),
            "checked_recordings": signal_data.get("checked", 0),
            "valid_recordings": signal_data.get("valid", 0)
        }
    
    return response

# ============================================================================
# WIFI CONFIGURATION ENDPOINTS
# ============================================================================

@app.post("/api/wifi/connect", tags=["wifi"])
async def connect_wifi(wifi_config: WiFiConfig):
    """
    Conectar a una red WiFi usando nmcli.
    
    Utiliza el comando nmcli del sistema para establecer una conexión
    WiFi con las credenciales proporcionadas.
    
    Args:
        wifi_config: Configuración WiFi con SSID y contraseña
        
    Returns:
        dict: Estado de la conexión y resultado del intento
        
    Example Request:
        ```json
        {
            "ssid": "Mi_Red_WiFi",
            "password": "mi_contraseña_segura"
        }
        ```
        
    Example Response:
        ```json
        {
            "success": true,
            "message": "WiFi connection attempt initiated",
            "status": "Connected successfully"
        }
        ```
        
    Raises:
        HTTPException: 500 para errores de conexión o configuración del sistema
    """
    try:
        status = wifi.proton_wifi_connect(ssid=wifi_config.ssid, password=wifi_config.password)
        return {
            "success": True,
            "message": "WiFi connection attempt initiated",
            "status": status
        }
    except Exception as e:
        logger.error(f"Error connecting to WiFi: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/wifi/status", tags=["wifi"])
async def get_wifi_status():
    """
    Obtener el estado actual de la conexión WiFi.
    
    Consulta el estado de conectividad WiFi del sistema usando nmcli
    para proporcionar información sobre la conexión activa.
    
    Returns:
        dict: Estado de la conexión WiFi actual
        
    Example Response:
        ```json
        {
            "success": true,
            "status": {
                "connected": true,
                "ssid": "Mi_Red_WiFi",
                "signal_strength": 85,
                "ip_address": "192.168.1.100"
            }
        }
        ```
        
    Raises:
        HTTPException: 500 para errores del sistema o comandos nmcli
    """
    try:
        status = wifi.proton_wifi_status()
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"Error getting WiFi status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/wifi/scan", tags=["wifi"])
async def scan_wifi_networks():
    """
    Escanear y listar redes WiFi disponibles.
    
    Realiza un escaneo activo de redes WiFi disponibles en el área
    usando nmcli para detectar puntos de acceso.
    
    Returns:
        dict: Lista de redes WiFi detectadas con información de señal
        
    Example Response:
        ```json
        {
            "success": true,
            "networks": [
                {
                    "ssid": "Red_Publica",
                    "signal": 90,
                    "security": "WPA2",
                    "frequency": "2.4GHz"
                },
                {
                    "ssid": "Red_Privada",
                    "signal": 65,
                    "security": "WPA3",
                    "frequency": "5GHz"
                }
            ]
        }
        ```
        
    Raises:
        HTTPException: 500 para errores del sistema o comandos nmcli
    """
    try:
        networks = wifi.proton_wifi_scan()
        return {
            "success": True,
            "networks": networks
        }
    except Exception as e:
        logger.error(f"Error scanning WiFi networks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================


def main():
    """
    Función principal para iniciar el servidor Uvicorn.
    
    Configura y ejecuta el servidor web FastAPI con las siguientes características:
    - Host: 127.0.0.1 (localhost)
    - Puerto: 8080
    - Recarga automática habilitada para desarrollo
    
    El servidor estará disponible en:
    - http://127.0.0.1:8080 (dashboard principal)
    - http://127.0.0.1:8080/docs (documentación automática de API)
    - http://127.0.0.1:8080/redoc (documentación alternativa)
    """
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )

if __name__ == "__main__":
    main()


