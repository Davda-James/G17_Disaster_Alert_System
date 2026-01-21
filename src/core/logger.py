"""
DAS Logger Module
Provides centralized logging for the Disaster Alert System.
Supports multiple log levels and outputs (console, file).
"""

import logging
import os
from datetime import datetime
from typing import Optional


class DASLogger:
    """
    Singleton logger for the Disaster Alert System.
    Implements structured logging with severity levels.
    """
    
    _instance: Optional['DASLogger'] = None
    _initialized: bool = False
    
    def __new__(cls, name: str = "DAS", log_level: int = logging.INFO):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, name: str = "DAS", log_level: int = logging.INFO):
        if DASLogger._initialized:
            return
            
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # Formatter with timestamp
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
        
        DASLogger._initialized = True
    
    def info(self, message: str) -> None:
        """Log INFO level message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log WARNING level message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log ERROR level message."""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log CRITICAL level message - used for disaster alerts."""
        self.logger.critical(message)
    
    def debug(self, message: str) -> None:
        """Log DEBUG level message."""
        self.logger.debug(message)
    
    def alert(self, disaster_type: str, severity: str, location: str) -> None:
        """
        Log a structured disaster alert.
        
        Args:
            disaster_type: Type of disaster (EARTHQUAKE, TSUNAMI, FLOOD, etc.)
            severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
            location: Geographic location of the disaster
        """
        alert_msg = f"DISASTER ALERT | Type: {disaster_type} | Severity: {severity} | Location: {location}"
        self.logger.critical(alert_msg)
    
    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        if cls._instance and hasattr(cls._instance, 'logger'):
            cls._instance.logger.handlers.clear()
        cls._instance = None
        cls._initialized = False
