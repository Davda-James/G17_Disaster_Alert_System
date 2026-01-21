"""
DAS Messaging Module
Implements SMS and Email gateways for alert notifications.
Includes failure mode simulation for testing reliability.
"""

import time
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from ..core.config import Config
from ..core.logger import DASLogger


class GatewayStatus(Enum):
    """Status codes for messaging gateways."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    INVALID_RECIPIENT = "INVALID_RECIPIENT"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


@dataclass
class NotificationResult:
    """Result of a notification attempt."""
    success: bool
    status: GatewayStatus
    message_id: Optional[str] = None
    timestamp: datetime = None
    retry_count: int = 0
    error_message: Optional[str] = None
    latency_ms: float = 0.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MessagingGateway(ABC):
    """Abstract base class for messaging gateways."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = DASLogger()
        self._sent_count = 0
        self._failed_count = 0
    
    @abstractmethod
    def send(self, recipient: str, message: str, priority: int = 1) -> NotificationResult:
        """Send a notification to a recipient."""
        pass
    
    @abstractmethod
    def send_bulk(self, recipients: List[str], message: str, priority: int = 1) -> List[NotificationResult]:
        """Send notifications to multiple recipients."""
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get gateway statistics."""
        total = self._sent_count + self._failed_count
        success_rate = (self._sent_count / total * 100) if total > 0 else 0.0
        return {
            "sent_count": self._sent_count,
            "failed_count": self._failed_count,
            "total_attempts": total,
            "success_rate": success_rate,
        }
    
    def _simulate_latency(self) -> float:
        """Simulate network latency if configured."""
        if self.config.simulate_high_latency:
            delay_seconds = self.config.latency_delay_ms / 1000.0
            time.sleep(delay_seconds)
            return self.config.latency_delay_ms
        return random.uniform(10, 100)  # Normal latency: 10-100ms


class SMSGateway(MessagingGateway):
    """
    SMS Gateway implementation.
    Simulates sending SMS alerts through a mobile network.
    """
    
    def __init__(self, config: Optional[Config] = None):
        super().__init__(config or Config.load_from_env())
        self.gateway_url = self.config.sms_gateway_url
    
    def send(self, recipient: str, message: str, priority: int = 1) -> NotificationResult:
        """
        Send an SMS to a single recipient.
        
        Args:
            recipient: Phone number in international format (e.g., +1234567890)
            message: Message content (max 160 chars for standard SMS)
            priority: 1-5 where 5 is highest priority
            
        Returns:
            NotificationResult with status
        """
        start_time = time.time()
        
        # Validate recipient
        if not self._validate_phone_number(recipient):
            return NotificationResult(
                success=False,
                status=GatewayStatus.INVALID_RECIPIENT,
                error_message=f"Invalid phone number format: {recipient}"
            )
        
        # Check for simulated network failure
        if self.config.simulate_network_failure:
            self._failed_count += 1
            return NotificationResult(
                success=False,
                status=GatewayStatus.SERVICE_UNAVAILABLE,
                error_message="Network failure (simulated)",
                latency_ms=0
            )
        
        # Simulate latency
        latency = self._simulate_latency()
        
        # Check timeout
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > self.config.api_timeout_seconds * 1000:
            self._failed_count += 1
            return NotificationResult(
                success=False,
                status=GatewayStatus.TIMEOUT,
                error_message=f"Request timed out after {self.config.api_timeout_seconds}s",
                latency_ms=elapsed_ms
            )
        
        # Simulate successful send
        self._sent_count += 1
        message_id = f"SMS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        
        self.logger.info(f"SMS sent to {recipient}: {message[:50]}...")
        
        return NotificationResult(
            success=True,
            status=GatewayStatus.SUCCESS,
            message_id=message_id,
            latency_ms=latency
        )
    
    def send_bulk(self, recipients: List[str], message: str, priority: int = 1) -> List[NotificationResult]:
        """Send SMS to multiple recipients."""
        results = []
        for recipient in recipients:
            result = self.send(recipient, message, priority)
            results.append(result)
        return results
    
    def _validate_phone_number(self, phone: str) -> bool:
        """Validate phone number format."""
        if not phone:
            return False
        # Basic validation: starts with + and contains 10-15 digits
        cleaned = phone.replace(" ", "").replace("-", "")
        if cleaned.startswith("+"):
            cleaned = cleaned[1:]
        return cleaned.isdigit() and 10 <= len(cleaned) <= 15


class EmailGateway(MessagingGateway):
    """
    Email Gateway implementation.
    Simulates sending email alerts through SMTP.
    """
    
    def __init__(self, config: Optional[Config] = None):
        super().__init__(config or Config.load_from_env())
        self.gateway_url = self.config.email_gateway_url
    
    def send(self, recipient: str, message: str, priority: int = 1, subject: str = "DAS Alert") -> NotificationResult:
        """
        Send an email to a single recipient.
        
        Args:
            recipient: Email address
            message: Email body content
            priority: 1-5 where 5 is highest priority
            subject: Email subject line
            
        Returns:
            NotificationResult with status
        """
        start_time = time.time()
        
        # Validate recipient
        if not self._validate_email(recipient):
            return NotificationResult(
                success=False,
                status=GatewayStatus.INVALID_RECIPIENT,
                error_message=f"Invalid email format: {recipient}"
            )
        
        # Check for simulated network failure
        if self.config.simulate_network_failure:
            self._failed_count += 1
            return NotificationResult(
                success=False,
                status=GatewayStatus.SERVICE_UNAVAILABLE,
                error_message="Network failure (simulated)",
                latency_ms=0
            )
        
        # Simulate latency
        latency = self._simulate_latency()
        
        # Simulate successful send
        self._sent_count += 1
        message_id = f"EMAIL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        
        self.logger.info(f"Email sent to {recipient}: {subject}")
        
        return NotificationResult(
            success=True,
            status=GatewayStatus.SUCCESS,
            message_id=message_id,
            latency_ms=latency
        )
    
    def send_bulk(self, recipients: List[str], message: str, priority: int = 1) -> List[NotificationResult]:
        """Send emails to multiple recipients."""
        results = []
        for recipient in recipients:
            result = self.send(recipient, message, priority)
            results.append(result)
        return results
    
    def _validate_email(self, email: str) -> bool:
        """Basic email validation."""
        if not email:
            return False
        # Must have @ with content on both sides
        if "@" not in email:
            return False
        parts = email.split("@")
        if len(parts) != 2:
            return False
        local_part, domain = parts
        # Local part must not be empty
        if not local_part:
            return False
        # Domain must have at least one dot
        if "." not in domain:
            return False
        return True


class NotificationService:
    """
    High-level notification service that coordinates multiple gateways.
    Implements retry logic and fallback mechanisms.
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.load_from_env()
        self.logger = DASLogger()
        self.sms_gateway = SMSGateway(self.config)
        self.email_gateway = EmailGateway(self.config)
        self._notification_log: List[Dict[str, Any]] = []
    
    def send_alert(
        self,
        message: str,
        phone_numbers: Optional[List[str]] = None,
        email_addresses: Optional[List[str]] = None,
        priority: int = 3
    ) -> Dict[str, Any]:
        """
        Send alert through all available channels.
        
        Args:
            message: Alert message content
            phone_numbers: List of phone numbers
            email_addresses: List of email addresses
            priority: Alert priority (1-5)
            
        Returns:
            Dictionary with results from all channels
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "priority": priority,
            "sms_results": [],
            "email_results": [],
            "overall_success": False,
        }
        
        # Send SMS alerts
        if phone_numbers:
            for phone in phone_numbers:
                result = self._send_with_retry(
                    lambda: self.sms_gateway.send(phone, message, priority)
                )
                results["sms_results"].append({
                    "recipient": phone,
                    "success": result.success,
                    "status": result.status.value,
                    "message_id": result.message_id,
                })
        
        # Send Email alerts
        if email_addresses:
            for email in email_addresses:
                result = self._send_with_retry(
                    lambda: self.email_gateway.send(email, message, priority, "🚨 DISASTER ALERT")
                )
                results["email_results"].append({
                    "recipient": email,
                    "success": result.success,
                    "status": result.status.value,
                    "message_id": result.message_id,
                })
        
        # Determine overall success - at least one notification must succeed
        # If no recipients provided at all, that's a failure
        has_any_recipients = bool(results["sms_results"]) or bool(results["email_results"])
        if not has_any_recipients:
            results["overall_success"] = False
        else:
            sms_success = any(r["success"] for r in results["sms_results"]) if results["sms_results"] else False
            email_success = any(r["success"] for r in results["email_results"]) if results["email_results"] else False
            results["overall_success"] = sms_success or email_success
        
        self._notification_log.append(results)
        return results
    
    def _send_with_retry(self, send_func) -> NotificationResult:
        """Execute send function with retry logic."""
        last_result = None
        
        for attempt in range(self.config.max_retry_attempts):
            result = send_func()
            last_result = result
            
            if result.success:
                return result
            
            if result.status == GatewayStatus.INVALID_RECIPIENT:
                # Don't retry for invalid recipients
                return result
            
            self.logger.warning(f"Notification attempt {attempt + 1} failed: {result.status.value}")
            
            # Exponential backoff
            if attempt < self.config.max_retry_attempts - 1:
                time.sleep(0.1 * (2 ** attempt))
        
        return last_result
    
    def get_notification_log(self) -> List[Dict[str, Any]]:
        """Get the notification log."""
        return self._notification_log.copy()
    
    def get_combined_statistics(self) -> Dict[str, Any]:
        """Get combined statistics from all gateways."""
        return {
            "sms_gateway": self.sms_gateway.get_statistics(),
            "email_gateway": self.email_gateway.get_statistics(),
            "total_notifications": len(self._notification_log),
        }
