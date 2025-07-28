"""
Módulo para manejo de base de datos SQLite para guardar resultados de predicciones
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PredictionDatabase:
    def __init__(self, db_path: str = "predictions.db"):
        """
        Inicializar la base de datos de predicciones
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        logger.info(f"Initializing PredictionDatabase with path: {os.path.abspath(self.db_path)}")
        self.init_database()
    
    def init_database(self):
        """Crear las tablas necesarias si no existen"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Crear tabla de predicciones
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        device_id TEXT NOT NULL,
                        device_name TEXT,
                        recording_id TEXT NOT NULL,
                        model_name TEXT NOT NULL,
                        channel INTEGER NOT NULL,
                        predicted_class TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        probabilities TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        error_message TEXT,
                        created_at TEXT NOT NULL,
                        UNIQUE(device_id, recording_id, model_name, channel)
                    )
                """)
                
                # Crear índices para mejorar performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_device_timestamp 
                    ON predictions(device_id, timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_model_class 
                    ON predictions(model_name, predicted_class)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_created_at 
                    ON predictions(created_at)
                """)
                
                conn.commit()
                logger.info(f"Database initialized at: {self.db_path}")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def save_prediction(self, 
                       device_id: str,
                       recording_id: str,
                       model_name: str,
                       channel: int,
                       prediction_result: Optional[Dict],
                       success: bool,
                       timestamp: Optional[str] = None,
                       error_message: Optional[str] = None,
                       device_name: Optional[str] = None) -> bool:
        """
        Guardar resultado de predicción en la base de datos
        
        Args:
            device_id: ID del dispositivo
            recording_id: ID de la grabación
            model_name: Nombre del modelo utilizado
            channel: Canal de la señal
            prediction_result: Resultado de la predicción con probabilidades
            success: Si la predicción fue exitosa
            timestamp: Timestamp de la grabación (opcional)
            error_message: Mensaje de error si falló (opcional)
            device_name: Nombre legible del dispositivo (opcional)
            
        Returns:
            bool: True si se guardó exitosamente
        """
        try:
            # Extraer información de la predicción
            if success and prediction_result:
                predicted_class = prediction_result.get("prediction", "unknown")
                probabilities = prediction_result.get("probabilities", {})
                confidence = max(probabilities.values()) if probabilities else 0.0
                probabilities_json = json.dumps(probabilities)
            else:
                predicted_class = "error"
                confidence = 0.0
                probabilities_json = "{}"
            
            # Usar timestamp actual si no se proporciona
            if not timestamp:
                timestamp = datetime.now().isoformat()
            
            created_at = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insertar o actualizar predicción
                cursor.execute("""
                    INSERT OR REPLACE INTO predictions 
                    (timestamp, device_id, device_name, recording_id, model_name, channel, 
                     predicted_class, confidence, probabilities, success, 
                     error_message, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp, device_id, device_name, recording_id, model_name, channel,
                    predicted_class, confidence, probabilities_json, success,
                    error_message, created_at
                ))
                
                conn.commit()
                logger.debug(f"Saved prediction for {device_id}/{recording_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving prediction: {e}")
            return False
    
    def get_predictions(self, 
                       device_id: Optional[str] = None,
                       model_name: Optional[str] = None,
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None,
                       limit: int = 100) -> List[Dict]:
        """
        Obtener predicciones de la base de datos
        
        Args:
            device_id: Filtrar por dispositivo (opcional)
            model_name: Filtrar por modelo (opcional)
            start_date: Fecha inicio (ISO format, opcional)
            end_date: Fecha fin (ISO format, opcional)
            limit: Número máximo de resultados
            
        Returns:
            List[Dict]: Lista de predicciones
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
                cursor = conn.cursor()
                
                # Construir query con filtros
                query = "SELECT * FROM predictions WHERE 1=1"
                params = []
                
                if device_id:
                    query += " AND device_id = ?"
                    params.append(device_id)
                
                if model_name:
                    query += " AND model_name = ?"
                    params.append(model_name)
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)
                
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date)
                
                query += " ORDER BY created_at DESC, timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Convertir a lista de diccionarios
                predictions = []
                for row in rows:
                    prediction = dict(row)
                    # Deserializar probabilidades JSON
                    prediction['probabilities'] = json.loads(prediction['probabilities'])
                    predictions.append(prediction)
                
                return predictions
                
        except Exception as e:
            logger.error(f"Error getting predictions: {e}")
            return []
    
    def get_prediction_stats(self, 
                            device_id: Optional[str] = None,
                            model_name: Optional[str] = None,
                            days_back: int = 7) -> Dict:
        """
        Obtener estadísticas de predicciones
        
        Args:
            device_id: Filtrar por dispositivo (opcional)
            model_name: Filtrar por modelo (opcional)
            days_back: Días hacia atrás para las estadísticas
            
        Returns:
            Dict: Estadísticas de predicciones
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Fecha límite
                from datetime import datetime, timedelta
                start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
                
                # Query base
                where_clause = "WHERE created_at >= ?"
                params = [start_date]
                
                if device_id:
                    where_clause += " AND device_id = ?"
                    params.append(device_id)
                
                if model_name:
                    where_clause += " AND model_name = ?"
                    params.append(model_name)
                
                # Total de predicciones
                cursor.execute(f"SELECT COUNT(*) FROM predictions {where_clause}", params)
                total_predictions = cursor.fetchone()[0]
                
                # Predicciones exitosas
                cursor.execute(f"SELECT COUNT(*) FROM predictions {where_clause} AND success = 1", params)
                successful_predictions = cursor.fetchone()[0]
                
                # Distribución por clase
                cursor.execute(f"""
                    SELECT predicted_class, COUNT(*) as count 
                    FROM predictions {where_clause} AND success = 1
                    GROUP BY predicted_class 
                    ORDER BY count DESC
                """, params)
                class_distribution = dict(cursor.fetchall())
                
                # Modelos más usados
                cursor.execute(f"""
                    SELECT model_name, COUNT(*) as count 
                    FROM predictions {where_clause}
                    GROUP BY model_name 
                    ORDER BY count DESC
                    LIMIT 5
                """, params)
                top_models = dict(cursor.fetchall())
                
                return {
                    "total_predictions": total_predictions,
                    "successful_predictions": successful_predictions,
                    "failed_predictions": total_predictions - successful_predictions,
                    "success_rate": (successful_predictions / total_predictions * 100) if total_predictions > 0 else 0,
                    "class_distribution": class_distribution,
                    "top_models": top_models,
                    "period_days": days_back
                }
                
        except Exception as e:
            logger.error(f"Error getting prediction stats: {e}")
            return {}
    
    def cleanup_old_predictions(self, days_to_keep: int = 30) -> int:
        """
        Limpiar predicciones antiguas
        
        Args:
            days_to_keep: Días de predicciones a mantener
            
        Returns:
            int: Número de registros eliminados
        """
        try:
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM predictions WHERE created_at < ?", (cutoff_date,))
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} old predictions")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up predictions: {e}")
            return 0
    
    def get_database_info(self) -> Dict:
        """
        Obtener información general de la base de datos
        
        Returns:
            Dict: Información de la base de datos
        """
        try:
            db_file = Path(self.db_path)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Contar registros totales
                cursor.execute("SELECT COUNT(*) FROM predictions")
                total_records = cursor.fetchone()[0]
                
                # Fecha más antigua y más reciente
                cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM predictions")
                min_date, max_date = cursor.fetchone()
                
                # Tamaño del archivo
                file_size = db_file.stat().st_size if db_file.exists() else 0
                
                return {
                    "database_path": str(db_file.absolute()),
                    "file_size_bytes": file_size,
                    "file_size_mb": round(file_size / 1024 / 1024, 2),
                    "total_records": total_records,
                    "oldest_record": min_date,
                    "newest_record": max_date
                }
                
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {}

    def delete_prediction(self, prediction_id: int) -> bool:
        """
        Eliminar una predicción específica de la base de datos
        
        Args:
            prediction_id: ID de la predicción a eliminar
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar si la predicción existe
                cursor.execute("SELECT COUNT(*) FROM predictions WHERE id = ?", (prediction_id,))
                if cursor.fetchone()[0] == 0:
                    logger.warning(f"Prediction {prediction_id} not found")
                    return False
                
                # Eliminar la predicción
                cursor.execute("DELETE FROM predictions WHERE id = ?", (prediction_id,))
                conn.commit()
                
                logger.info(f"Deleted prediction {prediction_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting prediction {prediction_id}: {e}")
            return False
