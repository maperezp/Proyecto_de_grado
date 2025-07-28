""" ProtonNG Ethernet Commands
"""

from fastapi import HTTPException
from modules import common as cm
from models.proton_models import EthernetConfig
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def proton_create_eth_connection(config: EthernetConfig):
    """
    Create or modify Ethernet connection using nmcli
    """
    try:
        # Delete existing connection for the interface
        ifdown_cmd = f"ifdown {config.interface} "
        cm.run_command(ifdown_cmd)

        # Check IP integrity
        if not all([config.ip_address, config.subnet_mask, config.gateway]):
            raise HTTPException(
                status_code=400, 
                detail="IP address, subnet mask, and gateway are required for manual configuration"
            )

        connect_cmd = (
            f"ifconfig {config.interface} "
            f"{config.ip_address} netmask {config.subnet_mask} "
            f"broadcast '{config.gateway}' "
        )

        # Execute connection command
        cm.run_command(connect_cmd)

        logger.info(f"Configured Ethernet connection for {config.interface}")
        return {"status": "success", "message": f"Configured {config.interface}"}

    except HTTPException as e:
        return {"status": "error", "message": str(e.detail)}


def proton_get_eth_status():
    try:
        # Get all eth interfaces
        interfaces_cmd = "ifconfig eth1; ifconfig eth0"
        eth_output = cm.run_command(interfaces_cmd)

        return {
            "interfaces": eth_output.split('\n')
        }
    except HTTPException as e:
        return {"status": "error", "message": str(e.detail)}

def get_available_interfaces():
    try:
        # Find Ethernet interfaces
        interfaces_cmd = "ls /sys/class/net | grep -E '^eth|^enp'"
        interfaces_output = cm.run_command(interfaces_cmd)

        return {"interfaces": interfaces_output.split('\n')}
    except HTTPException as e:
        return {"status": "error", "message": str(e.detail)}
