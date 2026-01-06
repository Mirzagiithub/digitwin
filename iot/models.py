from django.db import models
import uuid
from django.utils import timezone
from decimal import Decimal

from core.models import Organization, CustomUser
from assets.models import Asset


# -------------------------------------------------------------------
# Telemetry (HIGH VOLUME, READ-ONLY)
# -------------------------------------------------------------------
class TelemetryData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='telemetry'
    )
    metric = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=14, decimal_places=6)
    unit = models.CharField(max_length=20, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)
    quality_score = models.FloatField(default=1.0)

    class Meta:
        db_table = 'telemetry_data'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['asset', 'metric', '-timestamp']),
            models.Index(fields=['asset', '-timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.asset.asset_id}.{self.metric}={self.value}"


# -------------------------------------------------------------------
# Alerts (SYSTEM GENERATED – IMMUTABLE)
# -------------------------------------------------------------------
class Alert(models.Model):
    SEVERITY_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
        ('emergency', 'Emergency'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='info'
    )
    source = models.CharField(max_length=100)

    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['asset', '-created_at']),
            models.Index(fields=['severity', 'acknowledged']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.severity})"


# -------------------------------------------------------------------
# Devices
# -------------------------------------------------------------------
class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    device_id = models.CharField(max_length=100)
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='devices'
    )

    device_type = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=200, blank=True)
    model = models.CharField(max_length=100, blank=True)
    firmware_version = models.CharField(max_length=50, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=17, blank=True)

    protocol = models.CharField(
        max_length=20,
        choices=[
            ('mqtt', 'MQTT'),
            ('modbus', 'Modbus'),
            ('opcua', 'OPC-UA'),
            ('http', 'HTTP/REST'),
            ('websocket', 'WebSocket'),
            ('bacnet', 'BACnet'),
        ]
    )

    connection_status = models.CharField(
        max_length=20,
        choices=[
            ('connected', 'Connected'),
            ('disconnected', 'Disconnected'),
            ('error', 'Error'),
        ],
        default='disconnected'
    )

    last_seen = models.DateTimeField(null=True, blank=True)
    configuration = models.JSONField(default=dict, blank=True)
    capabilities = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devices'
        ordering = ['-created_at']
        unique_together = ['asset', 'device_id']
        indexes = [
            models.Index(fields=['asset', 'device_id']),
            models.Index(fields=['connection_status']),
        ]

    def __str__(self):
        return f"{self.device_id} ({self.device_type})"


# -------------------------------------------------------------------
# Sensors
# -------------------------------------------------------------------
class Sensor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='sensors'
    )

    sensor_id = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    sensor_type = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)

    sampling_rate = models.FloatField(help_text="Samples per second")
    precision = models.FloatField(null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)

    calibration_date = models.DateField(null=True, blank=True)
    calibration_due = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    configuration = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sensors'
        unique_together = ['device', 'sensor_id']
        indexes = [
            models.Index(fields=['device', 'sensor_id']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.sensor_id} - {self.name}"


# -------------------------------------------------------------------
# Commands (AUDIT LOG – IMMUTABLE)
# -------------------------------------------------------------------
class Command(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='commands'
    )

    command_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    issued_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    issued_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('executed', 'Executed'),
            ('failed', 'Failed'),
            ('timeout', 'Timeout'),
        ],
        default='pending'
    )

    response = models.JSONField(null=True, blank=True)
    response_received_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'commands'
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['device', '-issued_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.command_type} → {self.device.device_id}"
