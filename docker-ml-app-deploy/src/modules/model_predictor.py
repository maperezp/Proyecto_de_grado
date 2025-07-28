"""
Model predictor module for vibration analysis and prediction.
"""
import numpy as np
import pandas as pd
import joblib
import logging
from pathlib import Path
from typing import Dict, Optional
from scipy.fft import fft, fftfreq
from scipy.stats import skew, kurtosis

logger = logging.getLogger(__name__)

# Mapeo de números de clase a nombres
CLASS_NAMES = {
    0: 'normal',
    1: 'horizontal-misalignment', 
    2: 'vertical-misalignment',
    3: 'imbalance',
    4: 'ball_fault',
    5: 'cage_fault',
    6: 'outer_race'
}


class ModelPredictor:
    def __init__(self, models_path: Optional[str] = None):
        if models_path is None:
            # Obtener el directorio base del proyecto
            current_dir = Path(__file__).parent.parent  # modules -> src
            self.models_path = current_dir / "models"
        else:
            self.models_path = Path(models_path)
        self.models = {}
        self.load_models()
    
    def load_models(self):
        """Cargar modelos pre-entrenados"""
        try:
            if self.models_path.exists():
                for model_file in self.models_path.glob("*.joblib"):
                    model_name = model_file.stem
                    try:
                        self.models[model_name] = joblib.load(model_file)
                        logger.info(f"Model loaded: {model_name}")
                    except Exception as e:
                        logger.error(f"Error loading model {model_name}: {e}")
            else:
                logger.warning(f"Models path not found: {self.models_path}")
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def compute_basic_time_features(self, signal: np.ndarray) -> dict:
        """Compute time domain features for a signal"""
        mean_val = signal.mean()
        std_val = signal.std()
        rms_val = np.sqrt(np.mean(signal ** 2))
        max_val = np.max(signal)
        min_val = np.min(signal)
        peak_to_peak = max_val - min_val
        mean_abs = np.mean(np.abs(signal))

        features = {
            "mean": mean_val,
            "std": std_val,
            "rms": rms_val,
            "max": max_val,
            "min": min_val,
            "peak_to_peak": peak_to_peak,
            "mean_abs": mean_abs,
            "crest_factor": max_val / rms_val if rms_val > 0 else np.nan,
            "shape_factor": rms_val / mean_abs if mean_abs > 0 else np.nan,
            "impulse_factor": max_val / mean_abs if mean_abs > 0 else np.nan,
            "skewness": skew(signal),
            "kurtosis": kurtosis(signal),
            "energy": np.sum(signal ** 2),
            "zero_crossing_rate": np.sum(np.diff(np.sign(signal)) != 0) / len(signal)
        }

        return features

    def compute_frequency_features(self, signal: np.ndarray, sampling_rate: float) -> dict:
        """Compute frequency domain features for a signal"""
        N = len(signal)
        yf = fft(signal)
        xf = fftfreq(N, 1 / sampling_rate)[:N // 2]
        yf_half = np.array(yf[:N // 2])
        amplitudes = np.abs(yf_half) * 2 / N

        if len(amplitudes) == 0 or np.sum(amplitudes) == 0:
            return {
                "dominant_freq": np.nan,
                "dominant_amp": np.nan,
                "spectral_energy": np.nan,
                "spectral_centroid": np.nan,
                "spectral_bandwidth": np.nan,
                "spectral_flatness": np.nan,
            }

        dominant_idx = np.argmax(amplitudes)
        spectral_centroid_numerator = np.sum(xf * amplitudes)
        spectral_centroid_denominator = np.sum(amplitudes)

        centroid = spectral_centroid_numerator / spectral_centroid_denominator
        squared_diff = (xf - centroid) ** 2
        bandwidth = np.sqrt(np.sum(squared_diff * amplitudes) / spectral_centroid_denominator)

        nonzero_amps = amplitudes[amplitudes > 0]
        geometric_mean = np.exp(np.mean(np.log(nonzero_amps))) if len(nonzero_amps) > 0 else 0
        arithmetic_mean = np.mean(nonzero_amps) if len(nonzero_amps) > 0 else 0
        flatness = geometric_mean / arithmetic_mean if arithmetic_mean > 0 else np.nan

        features = {
            "dominant_freq": xf[dominant_idx],
            "dominant_amp": amplitudes[dominant_idx],
            "spectral_energy": np.sum(amplitudes ** 2),
            "spectral_centroid": centroid,
            "spectral_bandwidth": bandwidth,
            "spectral_flatness": flatness
        }
        return features
            
    def extract_features_from_multi_channel_data(self, samples_data: np.ndarray, sampling_rate: float = 25000) -> pd.DataFrame:
        """
        Extract features from multi-channel vibration data using the same method as training.
        samples_data should be a 2D array where each column is a sensor channel.
        Column order: [tachometer, underhang-axial, underhang-radial, underhang-tangential,
                      overhang-axial, overhang-radial, overhang-tangential, microphone]
        """
        column_names = [
            "tachometer", "underhang-axial", "underhang-radial", "underhang-tangential",
            "overhang-axial", "overhang-radial", "overhang-tangential"
        ]

        # If we have fewer columns than expected, pad with zeros or use available columns
        if samples_data.shape[1] < len(column_names):
            # Use available columns, pad rest with zeros if needed
            actual_columns = samples_data.shape[1]
            column_names = column_names[:actual_columns]
        
        # Create DataFrame (
        df = pd.DataFrame(samples_data[:, :len(column_names)], columns=column_names)
       
        # Extract time and frequency features for each column
        all_features = {}
        
        for col in df.columns:
            signal = np.array(df[col].values)
            
            # Time features
            time_features = self.compute_basic_time_features(signal)
            for feat_name, value in time_features.items():
                all_features[f"time_{feat_name}_{col}"] = value
            
            # Frequency features
            freq_features = self.compute_frequency_features(signal, sampling_rate)
            for feat_name, value in freq_features.items():
                all_features[f"freq_{feat_name}_{col}"] = value
        
        return pd.DataFrame([all_features])
        
    def extract_features_by_model_type(self, samples_data: np.ndarray, model_name: str, sampling_rate: float = 25000) -> pd.DataFrame:
        """
        Extract features according to the specific model type.
        """
        # Determinar el tipo de modelo basado en su nombre
        if "3axis" in model_name.lower():
            # Modelos 3axis esperan features de axial, radial, tangential (60 features)
            return self.extract_3axis_features(samples_data, sampling_rate)
        elif "axial" in model_name.lower():
            # Modelos axiales esperan solo features axiales (20 features)
            return self.extract_single_axis_features(samples_data, sampling_rate, "axial")
        elif "radial" in model_name.lower():
            # Modelos radiales esperan solo features radiales (20 features)  
            return self.extract_single_axis_features(samples_data, sampling_rate, "radial")
        elif "tangential" in model_name.lower():
            # Modelos tangenciales esperan solo features tangenciales (20 features)
            return self.extract_single_axis_features(samples_data, sampling_rate, "tangential")
        else:
            # Modelo base: todas las características (140 features)
            return self.extract_features_from_multi_channel_data(samples_data, sampling_rate)
    
    def extract_3axis_features(self, samples_data: np.ndarray, sampling_rate: float) -> pd.DataFrame:
        """
        Extract features for 3-axis models (axial, radial, tangential).
        Expected format: 60 features (20 features × 3 axes)
        """
        all_features = {}
        
        # Generar datos para 3 direcciones
        axes = ["axial", "radial", "tangential"]
        
        for i, axis in enumerate(axes):
            if samples_data.ndim == 1:
                # Si es 1D, usar los datos con pequeñas variaciones para cada eje
                if axis == "axial":
                    signal = samples_data
                elif axis == "radial": 
                    # Añadir variación para el eje radial
                    signal = samples_data + np.random.normal(0, 0.1 * np.std(samples_data), len(samples_data))
                else:  # tangential
                    # Añadir variación para el eje tangencial
                    signal = samples_data + np.random.normal(0, 0.15 * np.std(samples_data), len(samples_data))
            else:
                # Si es multi-dimensional, usar las columnas disponibles
                col_idx = min(i + 1, samples_data.shape[1] - 1)  # +1 para saltar tachometer
                signal = samples_data[:, col_idx]
            
            # Extraer características para este eje
            time_features = self.compute_basic_time_features(signal)
            freq_features = self.compute_frequency_features(signal, sampling_rate)
            
            # Añadir con nombres apropiados para modelo 3axis
            for feat_name, value in time_features.items():
                all_features[f"time_{feat_name}_{axis}"] = value
            
            for feat_name, value in freq_features.items():
                all_features[f"freq_{feat_name}_{axis}"] = value
        
        return pd.DataFrame([all_features])
    
    def extract_single_axis_features(self, samples_data: np.ndarray, sampling_rate: float, axis_type: str) -> pd.DataFrame:
        """
        Extract features for single-axis models (axial, radial, or tangential).
        Expected format: 20 features (14 time + 6 frequency)
        """
        # Usar los datos de entrada (si es 1D) o seleccionar una columna apropiada
        if samples_data.ndim == 1:
            signal = samples_data
        else:
            # Seleccionar columna basada en el tipo de eje
            if axis_type == "axial":
                col_idx = 1  
            elif axis_type == "radial":
                col_idx = 2  
            else:  # tangential
                col_idx = 3  
            
            col_idx = min(col_idx, samples_data.shape[1] - 1)
            signal = samples_data[:, col_idx]
        
        all_features = {}
        
        # Extraer características sin sufijos de eje (como esperan los modelos single-axis)
        time_features = self.compute_basic_time_features(signal)
        freq_features = self.compute_frequency_features(signal, sampling_rate)
        
        for feat_name, value in time_features.items():
            all_features[f"time_{feat_name}"] = value
        
        for feat_name, value in freq_features.items():
            all_features[f"freq_{feat_name}"] = value
        
        return pd.DataFrame([all_features])
    
    
    def preprocess_data(self, data: Dict, model_name: str, sampling_rate: float = 25000) -> pd.DataFrame:
        """Preprocesar datos para predicción usando el formato que corresponde al modelo"""
        try:
            if "samples" in data:
                samples = np.array(data["samples"])
                
                # Si los datos son 1D, asumimos que es un solo canal y lo replicamos para simular multi-canal
                if samples.ndim == 1:
                    # Crear datos multi-canal simulados (7 canales sin micrófono)
                    # En una implementación real, recibirías datos de múltiples sensores
                    n_channels = 7  # tachometer + 6 canales de vibración
                    multi_channel_data = np.zeros((len(samples), n_channels))
                    
                    # Usar los datos reales para algunos canales y añadir variaciones para otros
                    for i in range(n_channels):
                        if i == 0:  # tachometer (suele ser más estable)
                            multi_channel_data[:, i] = samples * 0.1  # Señal más pequeña
                        else:  # canales de vibración
                            # Añadir pequeñas variaciones a los datos reales
                            noise_factor = 0.1 + i * 0.05
                            multi_channel_data[:, i] = samples + np.random.normal(0, noise_factor * np.std(samples), len(samples))
                else:
                    multi_channel_data = samples
                
                # Extraer características según el tipo de modelo
                features_df = self.extract_features_by_model_type(multi_channel_data, model_name, sampling_rate)
                return features_df
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error preprocessing data: {e}")
            return pd.DataFrame()

    def predict(self, data: Dict, model_name: str = "myRF_3axis_25000") -> Dict:
        """Realizar predicción usando el formato correcto de características"""
        try:
            if model_name not in self.models:
                available_models = list(self.models.keys())
                if available_models:
                    model_name = available_models[0]
                    logger.warning(f"Model {model_name} not found, using {available_models[0]}")
                else:
                    return {"error": "No models available"}
            
            model = self.models[model_name]
            
            
            sampling_rate = 25000  # default
            # Extraer sampling rate del nombre del modelo si está disponible
            if "_" in model_name:
                parts = model_name.split("_")
                for part in parts:
                    if part.isdigit():
                        sampling_rate = int(part)
                        break
            
            features_df = self.preprocess_data(data, model_name, sampling_rate)
            
            if features_df.empty:
                return {"error": "No features extracted"}
            
            # Los modelos con pipeline esperan DataFrame con nombres de columnas específicos
            # No convertir a numpy array, mantener como DataFrame
            
            # Realizar predicción directamente con DataFrame
            prediction = model.predict(features_df)[0]
            
            # Convertir predicción numérica a nombre de clase
            if hasattr(prediction, 'item'):
                prediction_num = prediction.item()
            else:
                prediction_num = int(prediction) if str(prediction).isdigit() else prediction
            
            prediction_name = CLASS_NAMES.get(prediction_num, f"clase_{prediction_num}")
            
            # Si el modelo tiene predict_proba
            probabilities = None
            if hasattr(model, 'predict_proba'):
                proba_result = model.predict_proba(features_df)[0]
                probabilities = [float(p) for p in proba_result]  # Convertir a float nativo
                # Crear diccionario con nombres de clases y probabilidades
                if hasattr(model, 'classes_'):
                    prob_dict = {}
                    for cls_num, prob in zip(model.classes_, probabilities):
                        cls_name = CLASS_NAMES.get(int(cls_num), f"clase_{cls_num}")
                        prob_dict[cls_name] = float(prob)
                else:
                    # Si no hay clases definidas, usar índices como nombres
                    prob_dict = {CLASS_NAMES.get(i, f"clase_{i}"): float(prob) 
                               for i, prob in enumerate(probabilities)}
            else:
                prob_dict = None
            
            return {
                "prediction": prediction_name,
                "prediction_class": prediction_num,
                "probabilities": prob_dict,
                "model_used": model_name,
                "features_count": features_df.shape[1],
                "sampling_rate": sampling_rate
            }
            
        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            return {"error": str(e)}
