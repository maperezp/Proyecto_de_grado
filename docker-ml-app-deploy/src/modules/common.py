# Common module
from fastapi import HTTPException
import subprocess
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_command(command):
    """
    Run a shell command and return its output or raise an exception
    """
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Command executed: {command}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {command}")
        logger.error(f"Error: {e.stderr}")
        raise HTTPException(status_code=400, detail=f"Command failed: {e.stderr}")