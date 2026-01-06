from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal, getcontext
import logging

from .models import TelemetryData, Alert

logger = logging.getLogger(__name__)

# Ensure high precision for Decimal calculations
getcontext().prec = 28

ANOMALY_STD_THRESHOLD = Decimal('3.0')
HISTORY_LIMIT = 20
MIN_HISTORY_REQUIRED = 10


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=30, retry_kwargs={'max_retries': 3})
def check_telemetry_anomaly(self, telemetry_id):
    """
    Detect simple statistical anomalies for telemetry data.
    Runs asynchronously after telemetry ingestion.
    """
    try:
        telemetry = TelemetryData.objects.select_related('asset').get(id=telemetry_id)

        since = timezone.now() - timedelta(hours=24)

        historical_qs = (
            TelemetryData.objects
            .filter(
                asset=telemetry.asset,
                metric=telemetry.metric,
                timestamp__gte=since
            )
            .exclude(id=telemetry.id)
            .order_by('-timestamp')[:HISTORY_LIMIT]
        )

        values = [t.value for t in historical_qs]

        if len(values) < MIN_HISTORY_REQUIRED:
            return  # Not enough data for anomaly detection

        avg_value = sum(values) / Decimal(len(values))

        variance = sum((v - avg_value) ** 2 for v in values) / Decimal(len(values))
        std_dev = variance.sqrt()

        if std_dev == 0:
            return  # Avoid division by zero / meaningless anomaly

        threshold = ANOMALY_STD_THRESHOLD * std_dev

        if abs(telemetry.value - avg_value) > threshold:
            # Prevent duplicate anomaly alerts
            exists = Alert.objects.filter(
                asset=telemetry.asset,
                source='anomaly_detection',
                metadata__telemetry_id=str(telemetry.id)
            ).exists()

            if exists:
                return

            Alert.objects.create(
                asset=telemetry.asset,
                title=f'Anomaly detected: {telemetry.metric}',
                message=(
                    f'Value {telemetry.value} deviates significantly from '
                    f'expected average {avg_value}'
                ),
                severity='warning',
                source='anomaly_detection',
                metadata={
                    'telemetry_id': str(telemetry.id),
                    'metric': telemetry.metric,
                    'value': str(telemetry.value),
                    'average': str(avg_value),
                    'std_dev': str(std_dev),
                    'threshold': str(threshold),
                }
            )

    except TelemetryData.DoesNotExist:
        logger.warning(f"Telemetry {telemetry_id} not found for anomaly check")

    except Exception as exc:
        logger.exception("Telemetry anomaly detection failed")
        raise exc
