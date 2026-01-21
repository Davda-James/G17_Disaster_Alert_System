"""
DAS Alert Manager Module
Core logic for processing sensor data and triggering disaster alerts.
Implements Risk-Based prioritization for mission-critical scenarios.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Callable
from uuid import uuid4

from ..core.config import Config
from ..core.logger import DASLogger


class DisasterType(Enum):
    """Enumeration of supported disaster types."""
    EARTHQUAKE = "EARTHQUAKE"
    TSUNAMI = "TSUNAMI"
    FLOOD = "FLOOD"
    CYCLONE = "CYCLONE"
    WILDFIRE = "WILDFIRE"
    VOLCANIC_ERUPTION = "VOLCANIC_ERUPTION"
    LANDSLIDE = "LANDSLIDE"


class SeverityLevel(Enum):
    """
    Severity levels for alerts.
    Based on ISO 22324:2015 - Societal security guidelines.
    """
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    CATASTROPHIC = 5  # Reserved for life-threatening scenarios
    
    @classmethod
    def from_value(cls, value: float, disaster_type: DisasterType) -> 'SeverityLevel':
        """
        Determine severity based on sensor value and disaster type.
        Uses Risk-Based Testing (RBT) principles.
        """
        thresholds = {
            DisasterType.EARTHQUAKE: [(3.0, cls.LOW), (5.0, cls.MEDIUM), (6.5, cls.HIGH), (7.5, cls.CRITICAL), (8.5, cls.CATASTROPHIC)],
            DisasterType.TSUNAMI: [(0.5, cls.LOW), (2.0, cls.MEDIUM), (5.0, cls.HIGH), (10.0, cls.CRITICAL), (15.0, cls.CATASTROPHIC)],
            DisasterType.FLOOD: [(1.0, cls.LOW), (3.0, cls.MEDIUM), (5.0, cls.HIGH), (8.0, cls.CRITICAL), (10.0, cls.CATASTROPHIC)],
            DisasterType.CYCLONE: [(65, cls.LOW), (120, cls.MEDIUM), (180, cls.HIGH), (250, cls.CRITICAL), (300, cls.CATASTROPHIC)],
        }
        
        type_thresholds = thresholds.get(disaster_type, [(1, cls.LOW), (3, cls.MEDIUM), (5, cls.HIGH), (8, cls.CRITICAL), (10, cls.CATASTROPHIC)])
        
        for threshold, severity in reversed(type_thresholds):
            if value >= threshold:
                return severity
        return cls.LOW


@dataclass
class Alert:
    """
    Represents a disaster alert with full traceability.
    """
    alert_id: str = field(default_factory=lambda: str(uuid4()))
    disaster_type: DisasterType = DisasterType.EARTHQUAKE
    severity: SeverityLevel = SeverityLevel.LOW
    location: str = ""
    sensor_value: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    message: str = ""
    acknowledged: bool = False
    notification_sent: bool = False
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize alert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "disaster_type": self.disaster_type.value,
            "severity": self.severity.name,
            "severity_level": self.severity.value,
            "location": self.location,
            "sensor_value": self.sensor_value,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "acknowledged": self.acknowledged,
            "notification_sent": self.notification_sent,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
        }
    
    def __str__(self) -> str:
        return f"[{self.severity.name}] {self.disaster_type.value} at {self.location} - Value: {self.sensor_value}"


class AlertManager:
    """
    Central manager for processing sensor data and generating alerts.
    Implements the core business logic for the Disaster Alert System.
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.load_from_env()
        self.logger = DASLogger()
        self.alerts: List[Alert] = []
        self.notification_callbacks: List[Callable[[Alert], bool]] = []
        self._alert_history: List[Alert] = []
    
    def register_notification_callback(self, callback: Callable[[Alert], bool]) -> None:
        """
        Register a callback function to be invoked when an alert is triggered.
        The callback should return True if notification was successful.
        """
        self.notification_callbacks.append(callback)
    
    def process_sensor_data(
        self,
        disaster_type: DisasterType,
        sensor_value: float,
        location: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Alert]:
        """
        Process incoming sensor data and generate an alert if threshold is exceeded.
        
        Args:
            disaster_type: Type of disaster being monitored
            sensor_value: Raw sensor reading
            location: Geographic location of the sensor
            metadata: Additional context information
            
        Returns:
            Alert object if threshold exceeded, None otherwise
        """
        # Input validation - critical for safety systems
        if sensor_value < 0:
            self.logger.warning(f"Invalid negative sensor value received: {sensor_value}")
            return None
        
        if not location or not location.strip():
            self.logger.error("Empty location provided - cannot process alert")
            return None
        
        # Get threshold based on disaster type
        threshold = self._get_threshold(disaster_type)
        
        if sensor_value >= threshold:
            severity = SeverityLevel.from_value(sensor_value, disaster_type)
            
            alert = Alert(
                disaster_type=disaster_type,
                severity=severity,
                location=location.strip(),
                sensor_value=sensor_value,
                message=self._generate_alert_message(disaster_type, severity, location, sensor_value),
                metadata=metadata or {}
            )
            
            self.alerts.append(alert)
            self._alert_history.append(alert)
            
            self.logger.alert(disaster_type.value, severity.name, location)
            
            # Trigger notifications
            self._send_notifications(alert)
            
            return alert
        
        return None
    
    def _get_threshold(self, disaster_type: DisasterType) -> float:
        """Get the configured threshold for a disaster type."""
        thresholds = {
            DisasterType.EARTHQUAKE: self.config.earthquake_magnitude_threshold,
            DisasterType.TSUNAMI: self.config.tsunami_wave_height_threshold,
            DisasterType.FLOOD: self.config.flood_water_level_threshold,
            DisasterType.CYCLONE: self.config.cyclone_wind_speed_threshold,
        }
        return thresholds.get(disaster_type, 5.0)
    
    def _generate_alert_message(
        self,
        disaster_type: DisasterType,
        severity: SeverityLevel,
        location: str,
        sensor_value: float
    ) -> str:
        """Generate a human-readable alert message."""
        unit_map = {
            DisasterType.EARTHQUAKE: "magnitude",
            DisasterType.TSUNAMI: "meter wave height",
            DisasterType.FLOOD: "meter water level",
            DisasterType.CYCLONE: "km/h wind speed",
        }
        unit = unit_map.get(disaster_type, "units")
        
        if severity == SeverityLevel.CATASTROPHIC:
            prefix = "⚠️ CATASTROPHIC EMERGENCY"
        elif severity == SeverityLevel.CRITICAL:
            prefix = "🔴 CRITICAL ALERT"
        elif severity == SeverityLevel.HIGH:
            prefix = "🟠 HIGH PRIORITY ALERT"
        else:
            prefix = "🟡 ALERT"
        
        return f"{prefix}: {disaster_type.value} detected at {location}. Measured: {sensor_value} {unit}. Take immediate action."
    
    def _send_notifications(self, alert: Alert) -> bool:
        """
        Send notifications through all registered callbacks.
        Returns True if at least one notification succeeded.
        """
        success = False
        for callback in self.notification_callbacks:
            try:
                result = callback(alert)
                if result:
                    success = True
            except Exception as e:
                self.logger.error(f"Notification callback failed: {str(e)}")
                alert.retry_count += 1
        
        alert.notification_sent = success
        return success
    
    def get_active_alerts(self, severity_filter: Optional[SeverityLevel] = None) -> List[Alert]:
        """Get all active (unacknowledged) alerts, optionally filtered by severity."""
        active = [a for a in self.alerts if not a.acknowledged]
        if severity_filter:
            active = [a for a in active if a.severity.value >= severity_filter.value]
        return active
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                self.logger.info(f"Alert {alert_id} acknowledged")
                return True
        return False
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get statistics about alerts."""
        total = len(self._alert_history)
        by_type = {}
        by_severity = {}
        
        for alert in self._alert_history:
            type_key = alert.disaster_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            
            sev_key = alert.severity.name
            by_severity[sev_key] = by_severity.get(sev_key, 0) + 1
        
        return {
            "total_alerts": total,
            "active_alerts": len(self.get_active_alerts()),
            "by_disaster_type": by_type,
            "by_severity": by_severity,
            "notification_success_rate": self._calculate_notification_success_rate(),
        }
    
    def _calculate_notification_success_rate(self) -> float:
        """Calculate the success rate of notifications."""
        if not self._alert_history:
            return 0.0
        successful = sum(1 for a in self._alert_history if a.notification_sent)
        return (successful / len(self._alert_history)) * 100
    
    def clear_acknowledged_alerts(self) -> int:
        """Remove acknowledged alerts from active list. Returns count removed."""
        initial_count = len(self.alerts)
        self.alerts = [a for a in self.alerts if not a.acknowledged]
        return initial_count - len(self.alerts)
