"""
DAS Configuration Module
Manages system configuration from environment variables and defaults.
Supports simulation of failure modes for testing.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class Config:
    """
    Configuration container for the Disaster Alert System.
    All thresholds and settings are configurable via environment variables.
    """
    
    # Alert Thresholds (configurable for different regions)
    earthquake_magnitude_threshold: float = field(
        default_factory=lambda: float(os.getenv("DAS_EARTHQUAKE_THRESHOLD", "5.0"))
    )
    tsunami_wave_height_threshold: float = field(
        default_factory=lambda: float(os.getenv("DAS_TSUNAMI_THRESHOLD", "2.0"))
    )
    flood_water_level_threshold: float = field(
        default_factory=lambda: float(os.getenv("DAS_FLOOD_THRESHOLD", "3.0"))
    )
    cyclone_wind_speed_threshold: float = field(
        default_factory=lambda: float(os.getenv("DAS_CYCLONE_THRESHOLD", "120.0"))
    )
    
    # API Configuration
    sms_gateway_url: str = field(
        default_factory=lambda: os.getenv("DAS_SMS_GATEWAY", "https://api.sms-gateway.local/send")
    )
    email_gateway_url: str = field(
        default_factory=lambda: os.getenv("DAS_EMAIL_GATEWAY", "https://api.email-gateway.local/send")
    )
    api_timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv("DAS_API_TIMEOUT", "30"))
    )
    max_retry_attempts: int = field(
        default_factory=lambda: int(os.getenv("DAS_MAX_RETRIES", "3"))
    )
    
    # Database Configuration
    db_host: str = field(
        default_factory=lambda: os.getenv("DAS_DB_HOST", "localhost")
    )
    db_port: int = field(
        default_factory=lambda: int(os.getenv("DAS_DB_PORT", "5432"))
    )
    db_name: str = field(
        default_factory=lambda: os.getenv("DAS_DB_NAME", "das_alerts")
    )
    
    # Failure Mode Simulation Flags (for testing)
    simulate_network_failure: bool = field(
        default_factory=lambda: os.getenv("DAS_SIMULATE_NETWORK_FAILURE", "false").lower() == "true"
    )
    simulate_db_corruption: bool = field(
        default_factory=lambda: os.getenv("DAS_SIMULATE_DB_CORRUPTION", "false").lower() == "true"
    )
    simulate_high_latency: bool = field(
        default_factory=lambda: os.getenv("DAS_SIMULATE_HIGH_LATENCY", "false").lower() == "true"
    )
    latency_delay_ms: int = field(
        default_factory=lambda: int(os.getenv("DAS_LATENCY_DELAY_MS", "5000"))
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "earthquake_threshold": self.earthquake_magnitude_threshold,
            "tsunami_threshold": self.tsunami_wave_height_threshold,
            "flood_threshold": self.flood_water_level_threshold,
            "cyclone_threshold": self.cyclone_wind_speed_threshold,
            "sms_gateway": self.sms_gateway_url,
            "email_gateway": self.email_gateway_url,
            "api_timeout": self.api_timeout_seconds,
            "max_retries": self.max_retry_attempts,
            "db_host": self.db_host,
            "db_port": self.db_port,
            "db_name": self.db_name,
            "failure_modes": {
                "network_failure": self.simulate_network_failure,
                "db_corruption": self.simulate_db_corruption,
                "high_latency": self.simulate_high_latency,
            }
        }
    
    @classmethod
    def load_from_env(cls) -> 'Config':
        """Factory method to load configuration from environment."""
        return cls()
    
    def validate(self) -> bool:
        """
        Validate configuration values.
        Returns True if all values are within acceptable ranges.
        """
        validations = [
            self.earthquake_magnitude_threshold >= 0,
            self.earthquake_magnitude_threshold <= 10,
            self.tsunami_wave_height_threshold >= 0,
            self.flood_water_level_threshold >= 0,
            self.cyclone_wind_speed_threshold >= 0,
            self.api_timeout_seconds > 0,
            self.max_retry_attempts >= 0,
            self.db_port > 0,
            self.db_port <= 65535,
        ]
        return all(validations)
