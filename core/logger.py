import logging
import sys
from core.config import settings

def setup_logger(name: str = "execra") -> logging.Logger:
    """
    Configures and returns a logger instance with a standardized format.
    """
    logger = logging.getLogger(name)
    
    # Only add handler if not already present to avoid duplicate logs
    if not logger.handlers:
        logger.setLevel(settings.LOG_LEVEL)
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(settings.LOG_LEVEL)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
    return logger

# Primary logger instance
logger = setup_logger()
