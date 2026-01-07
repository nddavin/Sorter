"""
Notification System

Integrations for Slack, Microsoft Teams, Email, and Webhooks.
"""

import json
import smtplib
import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import threading

logger = logging.getLogger(__name__)


@dataclass
class NotificationMessage:
    """Represents a notification message."""
    title: str
    body: str
    severity: str = "info"  # info, warning, error, success
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    channels: List[str] = field(default_factory=list)


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    def send(self, message: NotificationMessage) -> bool:
        """Send a notification."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test the channel connection."""
        pass


class EmailChannel(NotificationChannel):
    """Email notification channel."""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_address: str,
        use_tls: bool = True
    ):
        """Initialize email channel."""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_address = from_address
        self.use_tls = use_tls

    def send(self, message: NotificationMessage) -> bool:
        """Send email notification."""
        try:
            msg = MIMEMultipart()
            msg['Subject'] = f"[{message.severity.upper()}] {message.title}"
            msg['From'] = self.from_address
            msg['To'] = ", ".join(message.channels) if message.channels else self.username

            # Add body
            msg.attach(MIMEText(message.body, 'plain'))

            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Email sent: {message.title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def test_connection(self) -> bool:
        """Test SMTP connection."""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
            return True
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False


class SlackChannel(NotificationChannel):
    """Slack notification channel."""

    def __init__(self, webhook_url: str, channel: str = None, username: str = "Sorter Bot"):
        """Initialize Slack channel."""
        self.webhook_url = webhook_url
        self.channel = channel
        self.username = username

    def send(self, message: NotificationMessage) -> bool:
        """Send Slack notification."""
        try:
            payload = {
                "username": self.username,
                "attachments": [
                    {
                        "color": self._get_color(message.severity),
                        "title": message.title,
                        "text": message.body,
                        "footer": "Sorter Notification System",
                        "ts": int(message.timestamp.timestamp())
                    }
                ]
            }

            if self.channel:
                payload["channel"] = self.channel

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            response.raise_for_status()
            logger.info(f"Slack notification sent: {message.title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    def _get_color(self, severity: str) -> str:
        """Get Slack color based on severity."""
        colors = {
            "info": "#36a64f",
            "warning": "#ff9800",
            "error": "#f44336",
            "success": "#4caf50"
        }
        return colors.get(severity, "#36a64f")

    def test_connection(self) -> bool:
        """Test Slack webhook connection."""
        try:
            response = requests.get(self.webhook_url, timeout=10)
            return response.status_code == 200 or response.status_code == 405
        except Exception as e:
            logger.error(f"Slack connection test failed: {e}")
            return False


class TeamsChannel(NotificationChannel):
    """Microsoft Teams notification channel."""

    def __init__(self, webhook_url: str):
        """Initialize Teams channel."""
        self.webhook_url = webhook_url

    def send(self, message: NotificationMessage) -> bool:
        """Send Teams notification."""
        try:
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": self._get_color(message.severity),
                "summary": message.title,
                "sections": [
                    {
                        "activityTitle": message.title,
                        "activitySubtitle": f"Sorter | {message.timestamp.isoformat()}",
                        "facts": [
                            {"name": "Severity", "value": message.severity.upper()}
                        ],
                        "markdown": True,
                        "text": message.body
                    }
                ]
            }

            # Add metadata as facts if present
            if message.metadata:
                for key, value in message.metadata.items():
                    payload["sections"][0]["facts"].append({
                        "name": key,
                        "value": str(value)
                    })

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            response.raise_for_status()
            logger.info(f"Teams notification sent: {message.title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}")
            return False

    def _get_color(self, severity: str) -> str:
        """Get Teams color based on severity."""
        colors = {
            "info": "0076D7",
            "warning": "FFB900",
            "error": "D13438",
            "success": "0078D4"
        }
        return colors.get(severity, "0076D7")

    def test_connection(self) -> bool:
        """Test Teams webhook connection."""
        try:
            response = requests.post(
                self.webhook_url,
                json={"text": "Test message"},
                timeout=10
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Teams connection test failed: {e}")
            return False


class WebhookChannel(NotificationChannel):
    """Generic webhook notification channel."""

    def __init__(
        self,
        webhook_url: str,
        headers: Dict[str, str] = None,
        auth: tuple = None
    ):
        """Initialize webhook channel."""
        self.webhook_url = webhook_url
        self.headers = headers or {}
        self.auth = auth

    def send(self, message: NotificationMessage) -> bool:
        """Send webhook notification."""
        try:
            payload = {
                "title": message.title,
                "body": message.body,
                "severity": message.severity,
                "timestamp": message.timestamp.isoformat(),
                "metadata": message.metadata
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
                auth=self.auth,
                timeout=30
            )

            response.raise_for_status()
            logger.info(f"Webhook notification sent: {message.title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            return False

    def test_connection(self) -> bool:
        """Test webhook connection."""
        try:
            response = requests.get(self.webhook_url, timeout=10)
            return response.status_code in [200, 301, 302, 405]
        except Exception as e:
            logger.error(f"Webhook connection test failed: {e}")
            return False


class NotificationManager:
    """Manages notification channels and message routing."""

    def __init__(self):
        """Initialize notification manager."""
        self.channels: Dict[str, NotificationChannel] = {}
        self._lock = threading.Lock()
        self.default_channels: List[str] = []

    def register_channel(self, name: str, channel: NotificationChannel) -> None:
        """Register a notification channel."""
        with self._lock:
            self.channels[name] = channel

    def send(
        self,
        title: str,
        body: str,
        severity: str = "info",
        channels: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, bool]:
        """Send notification to specified channels."""
        message = NotificationMessage(
            title=title,
            body=body,
            severity=severity,
            metadata=metadata or {},
            channels=channels or self.default_channels
        )

        results = {}
        channel_names = channels or list(self.channels.keys())

        for name in channel_names:
            channel = self.channels.get(name)
            if channel:
                results[name] = channel.send(message)
            else:
                logger.warning(f"Channel {name} not found")
                results[name] = False

        return results

    def send_to_all(self, message: NotificationMessage) -> Dict[str, bool]:
        """Send notification to all registered channels."""
        results = {}
        for name, channel in self.channels.items():
            results[name] = channel.send(message)
        return results

    def test_all_connections(self) -> Dict[str, bool]:
        """Test all registered channel connections."""
        results = {}
        for name, channel in self.channels.items():
            results[name] = channel.test_connection()
        return results


# Predefined notification templates
class NotificationTemplates:
    """Predefined notification templates."""

    @staticmethod
    def file_uploaded(filename: str, user: str, size: int) -> NotificationMessage:
        return NotificationMessage(
            title="File Uploaded",
            body=f"User {user} uploaded {filename} ({size / 1024:.1f} KB)",
            severity="info",
            metadata={"filename": filename, "user": user, "size": size}
        )

    @staticmethod
    def file_processed(filename: str, status: str) -> NotificationMessage:
        return NotificationMessage(
            title="File Processing Complete",
            body=f"File {filename} processing completed with status: {status}",
            severity="success" if status == "completed" else "error",
            metadata={"filename": filename, "status": status}
        )

    @staticmethod
    def backup_completed(backup_type: str, size: int, file_count: int) -> NotificationMessage:
        return NotificationMessage(
            title="Backup Completed",
            body=f"{backup_type.capitalize()} backup completed: {file_count} files, {size / 1024 / 1024:.1f} MB",
            severity="success",
            metadata={"backup_type": backup_type, "size": size, "file_count": file_count}
        )

    @staticmethod
    def storage_warning(used_percent: float, free_space: int) -> NotificationMessage:
        return NotificationMessage(
            title="Storage Warning",
            body=f"Storage usage at {used_percent:.1f}%. {free_space / 1024 / 1024:.1f} MB free.",
            severity="warning",
            metadata={"used_percent": used_percent, "free_space_mb": free_space / 1024 / 1024}
        )

    @staticmethod
    def security_alert(alert_type: str, details: str) -> NotificationMessage:
        return NotificationMessage(
            title=f"Security Alert: {alert_type}",
            body=details,
            severity="error",
            metadata={"alert_type": alert_type, "details": details}
        )


# Global notification manager
notification_manager = NotificationManager()
templates = NotificationTemplates()


def init_notification_channels() -> NotificationManager:
    """Initialize notification channels from environment."""
    from .config import settings

    # Email channel
    if settings.smtp_server:
        notification_manager.register_channel(
            "email",
            EmailChannel(
                smtp_server=settings.smtp_server,
                smtp_port=settings.smtp_port or 587,
                username=settings.smtp_user,
                password=settings.smtp_password,
                from_address=settings.email_from or settings.smtp_user
            )
        )

    # Slack channel
    if settings.slack_webhook_url:
        notification_manager.register_channel(
            "slack",
            SlackChannel(
                webhook_url=settings.slack_webhook_url,
                channel=settings.slack_channel
            )
        )

    # Teams channel
    if settings.teams_webhook_url:
        notification_manager.register_channel(
            "teams",
            TeamsChannel(webhook_url=settings.teams_webhook_url)
        )

    return notification_manager
