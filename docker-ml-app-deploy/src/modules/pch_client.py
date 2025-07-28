"""
PCH-Cloud client module for handling authentication and data retrieval.
"""
import os
import json
import requests
import urllib3
import logging
from datetime import datetime, timedelta
from typing import Dict, List

# Deshabilitar warnings SSL como en el código de referencia
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class PCHCloudClient:
    def __init__(self, config_path: str = "config"):
        self.config_path = config_path
        self.load_config()
        self.session = requests.Session()
        self.token = None
        
    def load_config(self):
        """Cargar configuración desde archivos JSON"""
        config_file = os.path.join(self.config_path, "config.json")
        hosts_file = os.path.join(self.config_path, "hosts.json")
        
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
            with open(hosts_file, 'r') as f:
                self.hosts = json.load(f)
        except FileNotFoundError as e:
            logger.error(f"Configuration file not found: {e}")
            # Configuración por defecto
            self.config = {
                "host": "pchcloud",
                "username": "demo",
                "password": "password",
                "delete_on_server": False,
                "query_passed_days": 1
            }
            self.hosts = {
                "pchcloud": {
                    "backend": "https://pchcloud.pch-engineering.dk/backend",
                    "usermanager": "https://pchcloud.pch-engineering.dk/usermanager",
                    "devicemanager": "https://pchcloud.pch-engineering.dk/devicemanager"
                }
            }
    
    def get_base_urls(self) -> Dict[str, str]:
        """Obtener URLs base para el host configurado"""
        host = self.config.get("host", "pchcloud")
        urls = self.hosts.get(host, {})
        
        if not urls:
            logger.error(f"Host '{host}' not found in hosts configuration")
            available_hosts = list(self.hosts.keys())
            logger.error(f"Available hosts: {available_hosts}")
        
        return urls
    
    async def login(self) -> bool:
        """Autenticarse en PCH-Cloud"""
        try:
            urls = self.get_base_urls()
            if not urls:
                logger.error("No URLs found for host configuration")
                return False
                
            login_url = f"{urls['usermanager']}/login"
            
            # Usar 'data' en lugar de 'json' como en el código de referencia
            payload = {
                "username": self.config["username"],
                "password": self.config["password"]
            }
            
            # Deshabilitar verificación SSL como en el código de referencia
            response = self.session.post(login_url, data=payload, verify=False)
            
            logger.info(f"Login attempt - Status: {response.status_code} {response.reason}")
            
            # El código de referencia espera 201 Created, no 200 OK
            if response.status_code == 201:  # requests.codes.created
                result = response.json()
                logger.info(f"Login response: {result}")
                
                # El token puede venir como 'session_token' o 'token'
                self.token = result.get("session_token") or result.get("token")
                if self.token:
                    logger.info("Login successful")
                    return True
                else:
                    logger.error("No session_token or token found in response")
                    logger.error(f"Available keys: {list(result.keys())}")
                    return False
            else:
                logger.error(f"Login failed: {response.status_code} - Expected 201 Created")
                if response.text:
                    logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    async def get_devices(self) -> List[Dict]:
        """Obtener lista de dispositivos"""
        try:
            if not self.token:
                logger.error("No token available - login first")
                return []
                
            urls = self.get_base_urls()
            if not urls:
                logger.error("No URLs found for host configuration")
                return []
                
            # Usar la ruta correcta del backend como en el código de referencia
            devices_url = f"{urls['backend']}/device/devices"
            
            # Usar session_token en data como en el código de referencia
            response = self.session.get(devices_url, data={'session_token': self.token}, verify=False)
            
            logger.info(f"Get devices - Status: {response.status_code} {response.reason}")
            
            if response.status_code == 200:
                devices = response.json()
                logger.info(f"Retrieved {len(devices)} devices")
                return devices
            else:
                logger.error(f"Failed to get devices: {response.status_code}")
                if response.text:
                    logger.error(f"Response: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            return []
    
    async def get_recordings(self, device_id: str, hours_back: int = 24) -> List[Dict]:
        """Obtener grabaciones de un dispositivo"""
        try:
            if not self.token:
                logger.error("No token available - login first")
                return []
                
            urls = self.get_base_urls()
            if not urls:
                logger.error("No URLs found for host configuration")
                return []
            
            # Calcular rango de tiempo - usar datetime directamente como en el código de referencia
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Usar la API correcta como en el código de referencia
            recordings_url = f"{urls['backend']}/timerecording/recordings"
            
            # El device_id debe separarse en deviceHostId.deviceId
            # Manejar diferentes formatos de device_id
            if '.' in device_id:
                parts = device_id.split('.')
                if len(parts) >= 3:
                    # Formato: "Cooling-Towers.rbofrjsy.PCH1272-2015100007"
                    device_host_id = '.'.join(parts[:-1])  # "Cooling-Towers.rbofrjsy"
                    device_id_part = parts[-1]             # "PCH1272-2015100007"
                else:
                    # Formato simple: "host.device"
                    device_host_id, device_id_part = device_id.split('.', 1)
            else:
                device_host_id = device_id
                device_id_part = device_id
            
            # Usar session_token como en el código de referencia
            data = {
                'session_token': self.token,
                'deviceHostId': device_host_id,
                'deviceId': device_id_part,
                'start': start_time.isoformat(),  # Convertir a ISO format string
                'end': end_time.isoformat()       # Convertir a ISO format string
            }
            
            logger.info(f"Requesting recordings for deviceHostId: {device_host_id}, deviceId: {device_id_part}")
            logger.info(f"Time range: {start_time} to {end_time}")
            
            response = self.session.get(recordings_url, params=data, verify=False)  # Usar params en lugar de data
            
            logger.info(f"Get recordings - Status: {response.status_code} {response.reason}")
            logger.info(f"Request URL: {response.url}")
            
            if response.status_code == 200:
                recordings = response.json()
                logger.info(f"Retrieved {len(recordings)} recordings")
                
                # Agregar información de debugging para cada recording
                for i, recording in enumerate(recordings[:3]):  # Solo los primeros 3 para debugging
                    logger.info(f"Recording {i}: ID={recording.get('id')}, channels={recording.get('numberOfChannels', 'unknown')}")
                    if recording.get('parameters'):
                        logger.info(f"  Parameters: {[p.get('name') + '=' + str(p.get('value')) for p in recording['parameters'][:3]]}")
                
                return recordings
            else:
                logger.error(f"Failed to get recordings: {response.status_code}")
                if response.text:
                    logger.error(f"Response: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting recordings: {e}")
            return []
    
    async def get_recording_data(self, device_id: str, recording_id: str, channel: int = 1) -> Dict:
        """Obtener datos de una grabación específica"""
        try:
            if not self.token:
                logger.error("No token available - login first")
                return {}
                
            urls = self.get_base_urls()
            if not urls:
                logger.error("No URLs found for host configuration")
                return {}
            
            # Usar la API correcta como en el código de referencia
            data_url = f"{urls['backend']}/timerecording/recording/channel/raw"
            
            # El device_id debe separarse en deviceHostId.deviceId - usar la misma lógica
            if '.' in device_id:
                parts = device_id.split('.')
                if len(parts) >= 3:
                    # Formato: "Cooling-Towers.rbofrjsy.PCH1272-2015100007"
                    device_host_id = '.'.join(parts[:-1])  # "Cooling-Towers.rbofrjsy"
                    device_id_part = parts[-1]             # "PCH1272-2015100007"
                else:
                    # Formato simple: "host.device"
                    device_host_id, device_id_part = device_id.split('.', 1)
            else:
                device_host_id = device_id
                device_id_part = device_id
            
            # Usar session_token como en el código de referencia
            data = {
                'session_token': self.token,
                'recordingId': recording_id,
                'deviceHostId': device_host_id,
                'deviceId': device_id_part,
                'channel': channel
            }
            
            logger.info(f"Requesting recording data for deviceHostId: {device_host_id}, deviceId: {device_id_part}, recordingId: {recording_id}, channel: {channel}")
            
            response = self.session.get(data_url, data=data, verify=False)
            
            logger.info(f"Get recording data - Status: {response.status_code} {response.reason}")
            
            if response.status_code == 200:
                recording_data = response.json()
                logger.info(f"Retrieved recording data with {len(recording_data.get('samples', []))} samples")
                return recording_data
            else:
                logger.error(f"Failed to get recording data: {response.status_code}")
                if response.text:
                    logger.error(f"Response: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting recording data: {e}")
            return {}
