"""
Plot utilities module for generating visualization data.
"""
import json
import numpy as np
import plotly.graph_objects as go
import plotly.utils
import plotly
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PlotGenerator:
    @staticmethod
    def generate_time_plot(samples: list, delta: float, device_id: str) -> Dict[str, Any]:
        """Generate time domain plot data"""
        try:
            # Convertir samples a numpy array
            samples_array = np.array(samples)
            
            # Crear serie temporal
            time_axis = np.arange(len(samples_array)) * delta
            
            # Convertir a listas de Python para JSON serialization
            time_list = time_axis.tolist()
            samples_list = samples_array.tolist()
            
            # Crear gráfico con Plotly
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=time_list,
                y=samples_list,
                mode='lines',
                name='Vibration Signal',
                line=dict(width=1)
            ))
            
            fig.update_layout(
                title=f'Vibration Data - Device: {device_id}',
                xaxis_title='Time (s)',
                yaxis_title='Amplitude',
                hovermode='x'
            )
            
            return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
            
        except Exception as e:
            logger.error(f"Error generating time plot: {e}")
            return {}
    
    @staticmethod
    def generate_fft_plot(samples: list, delta: float, device_id: str) -> Dict[str, Any]:
        """Generate FFT plot data"""
        try:
            # Convertir samples a numpy array
            samples_array = np.array(samples)
            
            # Crear FFT
            fft = np.fft.fft(samples_array)
            freqs = np.fft.fftfreq(len(samples_array), delta)
            magnitude = np.abs(fft)
            
            # Solo tomar la mitad positiva del espectro
            half_idx = len(freqs) // 2
            freqs_positive = freqs[:half_idx]
            magnitude_positive = magnitude[:half_idx]
            
            # Convertir a listas de Python para JSON serialization
            freqs_list = freqs_positive.tolist()
            magnitude_list = magnitude_positive.tolist()
            
            fig_fft = go.Figure()
            fig_fft.add_trace(go.Scatter(
                x=freqs_list,
                y=magnitude_list,
                mode='lines',
                name='FFT Magnitude',
                line=dict(width=1)
            ))
            
            fig_fft.update_layout(
                title=f'FFT Spectrum - Device: {device_id}',
                xaxis_title='Frequency (Hz)',
                yaxis_title='Magnitude',
                hovermode='x'
            )
            
            return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig_fft))
            
        except Exception as e:
            logger.error(f"Error generating FFT plot: {e}")
            return {}
    
    @staticmethod
    def calculate_stats(samples: list, delta: float) -> Dict[str, Any]:
        """Calculate signal statistics"""
        try:
            samples_array = np.array(samples)
            return {
                "samples_count": len(samples),
                "duration": len(samples) * delta,
                "sampling_rate": 1/delta,
                "rms": float(np.sqrt(np.mean(samples_array**2))),
                "peak": float(np.max(np.abs(samples_array)))
            }
        except Exception as e:
            logger.error(f"Error calculating stats: {e}")
            return {}
