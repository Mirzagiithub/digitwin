from django.db import models
from django.utils import timezone
from django.conf import settings
import uuid

from core.models import Organization
from assets.models import Asset


# ============================
# SECURITY DIGITAL TWIN
# ============================
class SecurityDigitalTwin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='security_twins'
    )

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name='security_twin'
    )

    twin_type = models.CharField(
        max_length=50,
        choices=[
            ('full_replica', 'Full Security Replica'),
            ('behavioral', 'Behavioral Twin'),
            ('network', 'Network Security Twin'),
            ('endpoint', 'Endpoint Security Twin'),
            ('application', 'Application Security Twin'),
        ],
        default='behavioral'
    )

    security_score = models.FloatField(default=100.0)

    risk_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='low'
    )

    zero_trust_status = models.CharField(
        max_length=20,
        choices=[
            ('enforced', 'Enforced'),
            ('partial', 'Partial'),
            ('planned', 'Planned'),
            ('not_applicable', 'N/A'),
        ],
        default='planned'
    )

    security_controls = models.JSONField(default=dict)
    compliance_status = models.JSONField(default=dict)

    behavioral_baseline = models.JSONField(default=dict)
    baseline_established = models.BooleanField(default=False)
    baseline_confidence = models.FloatField(default=0.0)

    threat_indicators = models.JSONField(default=list, blank=True)
    active_threats = models.JSONField(default=list, blank=True)

    last_security_scan = models.DateTimeField(null=True, blank=True)
    last_sync = models.DateTimeField(null=True, blank=True)

    sync_status = models.CharField(
        max_length=20,
        choices=[
            ('synced', 'Synced'),
            ('out_of_sync', 'Out of Sync'),
            ('error', 'Error'),
            ('never_synced', 'Never Synced'),
        ],
        default='never_synced'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'security_digital_twins'
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.asset.name} Security Twin'


# ============================
# ZERO TRUST POLICY
# ============================
class ZeroTrustPolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='zero_trust_policies'
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    assets = models.ManyToManyField(
        Asset,
        related_name='zero_trust_policies',
        blank=True
    )

    framework = models.CharField(
        max_length=50,
        choices=[
            ('nist_800_207', 'NIST 800-207'),
            ('cisa', 'CISA'),
            ('forrester', 'Forrester'),
            ('beyondcorp', 'BeyondCorp'),
            ('custom', 'Custom'),
        ],
        default='custom'
    )

    enforcement_mode = models.CharField(
        max_length=20,
        choices=[
            ('monitor', 'Monitor'),
            ('block', 'Block'),
            ('adaptive', 'Adaptive'),
        ],
        default='monitor'
    )

    is_active = models.BooleanField(default=True)

    enforcement_status = models.CharField(
        max_length=20,
        choices=[
            ('not_enforced', 'Not Enforced'),
            ('partial', 'Partial'),
            ('fully_enforced', 'Fully Enforced'),
        ],
        default='not_enforced'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_zero_trust_policies'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'zero_trust_policies'
        ordering = ['-created_at']
        unique_together = ('organization', 'name')

    def __str__(self):
        return self.name


# ============================
# THREAT DETECTION RULE
# ============================
class ThreatDetectionRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='threat_rules'
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    rule_type = models.CharField(
        max_length=50,
        choices=[
            ('signature', 'Signature'),
            ('anomaly', 'Anomaly'),
            ('behavioral', 'Behavioral'),
            ('ml', 'Machine Learning'),
        ]
    )

    detection_logic = models.JSONField(default=dict)

    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium'
    )

    confidence = models.FloatField(default=0.8)

    is_active = models.BooleanField(default=True)

    detection_count = models.IntegerField(default=0)
    false_positive_count = models.IntegerField(default=0)
    last_triggered = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_threat_rules'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'threat_detection_rules'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


# ============================
# THREAT DETECTION EVENT
# ============================
class ThreatDetectionEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='threat_events'
    )

    rule = models.ForeignKey(
        ThreatDetectionRule,
        on_delete=models.CASCADE,
        related_name='events'
    )

    asset = models.ForeignKey(
        Asset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    timestamp = models.DateTimeField(default=timezone.now)
    severity = models.CharField(max_length=20)
    confidence = models.FloatField()

    telemetry_data = models.JSONField(default=dict)

    response_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('executed', 'Executed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )

    investigated = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'threat_detection_events'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.rule.name} @ {self.timestamp}'


# ============================
# ATTACK CAMPAIGN
# ============================
class AttackCampaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='attack_campaigns'
    )

    name = models.CharField(max_length=200)
    description = models.TextField()

    campaign_type = models.CharField(
        max_length=50,
        choices=[
            ('red_team', 'Red Team'),
            ('pentest', 'Penetration Test'),
            ('threat_hunting', 'Threat Hunting'),
        ]
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('planned', 'Planned'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='planned'
    )

    target_assets = models.ManyToManyField(
        Asset,
        related_name='attack_campaigns',
        blank=True
    )

    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='attack_campaigns',
        blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_attack_campaigns'
    )

    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attack_campaigns'
        ordering = ['-scheduled_start']

    def clean(self):
        if self.scheduled_end <= self.scheduled_start:
            raise ValueError('Scheduled end must be after scheduled start')

    def __str__(self):
        return self.name
