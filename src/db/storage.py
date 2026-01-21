"""
DAS Storage Module
Implements database operations with fallback cache for emergency contacts.
Simulates database corruption scenarios for testing.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..core.config import Config
from ..core.logger import DASLogger


@dataclass
class EmergencyContact:
    """Represents an emergency contact."""
    contact_id: str
    name: str
    phone: str
    email: str
    region: str
    priority_level: int = 1  # 1 = highest priority
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "contact_id": self.contact_id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "region": self.region,
            "priority_level": self.priority_level,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmergencyContact':
        """Create from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        return cls(
            contact_id=data["contact_id"],
            name=data["name"],
            phone=data["phone"],
            email=data["email"],
            region=data["region"],
            priority_level=data.get("priority_level", 1),
            active=data.get("active", True),
            created_at=created_at or datetime.now(),
        )


@dataclass
class AlertRecord:
    """Represents a stored alert record."""
    record_id: str
    alert_id: str
    disaster_type: str
    severity: str
    location: str
    sensor_value: float
    timestamp: datetime
    notifications_sent: int
    notifications_failed: int
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "record_id": self.record_id,
            "alert_id": self.alert_id,
            "disaster_type": self.disaster_type,
            "severity": self.severity,
            "location": self.location,
            "sensor_value": self.sensor_value,
            "timestamp": self.timestamp.isoformat(),
            "notifications_sent": self.notifications_sent,
            "notifications_failed": self.notifications_failed,
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
        }


class DatabaseException(Exception):
    """Custom exception for database operations."""
    pass


class DatabaseCorruptionException(DatabaseException):
    """Raised when database corruption is detected."""
    pass


class DatabaseManager:
    """
    Manages database operations for the Disaster Alert System.
    Implements a mock in-memory database with fallback cache.
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.load_from_env()
        self.logger = DASLogger()
        
        # In-memory storage (simulates primary database)
        self._contacts: Dict[str, EmergencyContact] = {}
        self._alerts: Dict[str, AlertRecord] = {}
        
        # Fallback cache (file-based for disaster scenarios)
        self._cache_dir = Path("./cache")
        self._cache_dir.mkdir(exist_ok=True)
        self._contacts_cache_file = self._cache_dir / "emergency_contacts_cache.json"
        
        self._connected = False
        self._corruption_detected = False
    
    def connect(self) -> bool:
        """
        Establish database connection.
        Simulates connection to PostgreSQL/MongoDB.
        """
        if self.config.simulate_db_corruption:
            self._corruption_detected = True
            self.logger.error("Database corruption detected! Falling back to cache.")
            return self._load_from_cache()
        
        self._connected = True
        self.logger.info(f"Connected to database: {self.config.db_host}:{self.config.db_port}")
        return True
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self._connected:
            self._save_to_cache()  # Backup to cache before disconnect
            self._connected = False
            self.logger.info("Database disconnected")
    
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._connected
    
    def is_using_fallback(self) -> bool:
        """Check if system is using fallback cache due to corruption."""
        return self._corruption_detected
    
    # Emergency Contact Operations
    
    def add_contact(self, contact: EmergencyContact) -> bool:
        """Add an emergency contact."""
        self._check_connection()
        
        if contact.contact_id in self._contacts:
            self.logger.warning(f"Contact {contact.contact_id} already exists")
            return False
        
        self._contacts[contact.contact_id] = contact
        self._save_to_cache()  # Always backup to cache
        self.logger.info(f"Added contact: {contact.name} ({contact.contact_id})")
        return True
    
    def get_contact(self, contact_id: str) -> Optional[EmergencyContact]:
        """Get a contact by ID."""
        self._check_connection()
        return self._contacts.get(contact_id)
    
    def get_contacts_by_region(self, region: str) -> List[EmergencyContact]:
        """Get all active contacts for a region."""
        self._check_connection()
        return [
            c for c in self._contacts.values()
            if c.region.lower() == region.lower() and c.active
        ]
    
    def get_all_contacts(self, active_only: bool = True) -> List[EmergencyContact]:
        """Get all contacts, optionally filtered by active status."""
        self._check_connection()
        contacts = list(self._contacts.values())
        if active_only:
            contacts = [c for c in contacts if c.active]
        return sorted(contacts, key=lambda c: c.priority_level)
    
    def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> bool:
        """Update a contact."""
        self._check_connection()
        
        if contact_id not in self._contacts:
            return False
        
        contact = self._contacts[contact_id]
        for key, value in updates.items():
            if hasattr(contact, key):
                setattr(contact, key, value)
        
        self._save_to_cache()
        return True
    
    def delete_contact(self, contact_id: str) -> bool:
        """Delete a contact (soft delete - sets active=False)."""
        self._check_connection()
        
        if contact_id not in self._contacts:
            return False
        
        self._contacts[contact_id].active = False
        self._save_to_cache()
        return True
    
    # Alert Record Operations
    
    def store_alert(self, record: AlertRecord) -> bool:
        """Store an alert record."""
        self._check_connection()
        
        self._alerts[record.record_id] = record
        self.logger.info(f"Stored alert record: {record.record_id}")
        return True
    
    def get_alert(self, record_id: str) -> Optional[AlertRecord]:
        """Get an alert record by ID."""
        self._check_connection()
        return self._alerts.get(record_id)
    
    def get_alerts_by_location(self, location: str) -> List[AlertRecord]:
        """Get all alerts for a location."""
        self._check_connection()
        return [
            a for a in self._alerts.values()
            if location.lower() in a.location.lower()
        ]
    
    def get_unacknowledged_alerts(self) -> List[AlertRecord]:
        """Get all unacknowledged alerts."""
        self._check_connection()
        return [a for a in self._alerts.values() if not a.acknowledged]
    
    def acknowledge_alert(self, record_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert."""
        self._check_connection()
        
        if record_id not in self._alerts:
            return False
        
        self._alerts[record_id].acknowledged = True
        self._alerts[record_id].acknowledged_by = acknowledged_by
        self._alerts[record_id].acknowledged_at = datetime.now()
        return True
    
    # Cache Operations (Fallback for disaster scenarios)
    
    def _save_to_cache(self) -> bool:
        """Save contacts to cache file."""
        try:
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "contacts": [c.to_dict() for c in self._contacts.values()],
            }
            with open(self._contacts_cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save cache: {str(e)}")
            return False
    
    def _load_from_cache(self) -> bool:
        """Load contacts from cache file."""
        try:
            if not self._contacts_cache_file.exists():
                self.logger.warning("No cache file found")
                return False
            
            with open(self._contacts_cache_file, "r") as f:
                cache_data = json.load(f)
            
            for contact_data in cache_data.get("contacts", []):
                contact = EmergencyContact.from_dict(contact_data)
                self._contacts[contact.contact_id] = contact
            
            self.logger.info(f"Loaded {len(self._contacts)} contacts from cache")
            self._connected = True  # Connected via cache fallback
            return True
        except Exception as e:
            self.logger.error(f"Failed to load cache: {str(e)}")
            return False
    
    def _check_connection(self) -> None:
        """Verify database connection, raise exception if not connected."""
        if self._corruption_detected and not self._connected:
            raise DatabaseCorruptionException(
                "Database is corrupted and no fallback cache available"
            )
        if not self._connected:
            raise DatabaseException("Not connected to database")
    
    # Statistics
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        return {
            "connected": self._connected,
            "using_fallback": self._corruption_detected,
            "total_contacts": len(self._contacts),
            "active_contacts": len([c for c in self._contacts.values() if c.active]),
            "total_alerts": len(self._alerts),
            "unacknowledged_alerts": len(self.get_unacknowledged_alerts()) if self._connected else 0,
        }
