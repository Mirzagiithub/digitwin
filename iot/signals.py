from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Alert, TelemetryData
from core.models import AuditLog

@receiver(post_save, sender=Alert)
def alert_created_handler(sender, instance, created, **kwargs):
    if created:
        # Log alert creation
        AuditLog.objects.create(
            organization=instance.asset.organization,
            user=instance.acknowledged_by if instance.acknowledged_by else None,
            action='ALERT_CREATED',
            model='Alert',
            object_id=str(instance.id),
            after_state={
                'title': instance.title,
                'severity': instance.severity,
                'asset': str(instance.asset.id),
            },
            ip_address='system',
            user_agent='system'
        )
        
        # Here you could add notification logic
        # send_alert_notification.delay(str(instance.id))

@receiver(post_save, sender=TelemetryData)
def telemetry_anomaly_check(sender, instance, created, **kwargs):
    if created:
        # Basic anomaly detection
        from .tasks import check_telemetry_anomaly
        check_telemetry_anomaly.delay(str(instance.id))
