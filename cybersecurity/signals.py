from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps

from .models import ThreatDetectionEvent
from core.models import AuditLog


@receiver(post_save, sender=ThreatDetectionEvent)
def threat_detection_handler(sender, instance, created, **kwargs):
    """
    Handle threat detection events safely.
    - No recursion
    - No hard dependency on IoT
    - Organization-aware
    """

    if not created:
        return

    # ============================
    # OPTIONAL ALERT CREATION
    # ============================
    Alert = apps.get_model('iot', 'Alert')

    alert_id = None
    if Alert:
        try:
            alert = Alert.objects.create(
                asset=instance.asset,
                title=f"Threat Detected: {instance.rule.name}",
                message=f"Threat detected with severity {instance.severity}",
                severity=instance.severity,
                source='threat_detection',
                metadata={
                    'rule_id': str(instance.rule.id),
                    'rule_name': instance.rule.name,
                    'confidence': instance.confidence,
                },
            )
            alert_id = str(alert.id)
        except Exception:
            # Never break security pipeline due to alert failure
            alert_id = None

    # ============================
    # AUDIT LOG (SYSTEM EVENT)
    # ============================
    AuditLog.objects.create(
        organization=instance.organization,
        user=None,  # system-generated
        action='THREAT_DETECTED',
        model='ThreatDetectionEvent',
        object_id=str(instance.id),
        after_state={
            'rule': instance.rule.name,
            'asset': str(instance.asset.id) if instance.asset else None,
            'severity': instance.severity,
            'alert_id': alert_id,
        },
        ip_address='0.0.0.0',
        user_agent='system',
    )
