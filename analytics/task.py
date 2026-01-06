from celery import shared_task
from django.utils import timezone
from django.db import transaction
from datetime import timedelta

from .models import Report, KPI, KPIValue
from core.models import Organization


# ============================
# REPORT GENERATION
# ============================
@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=10, retry_kwargs={'max_retries': 3})
def generate_report_task(self, report_id):
    """
    Generate a report safely (idempotent & retry-safe)
    """
    with transaction.atomic():
        report = Report.objects.select_for_update().get(id=report_id)

        if report.status == 'completed':
            return str(report.id)

        report.status = 'generating'
        report.save(update_fields=['status'])

    # ---- Simulated generation logic (replace later) ----
    report_data = {
        'generated_at': timezone.now().isoformat(),
        'parameters': report.parameters,
        'summary': {
            'total_assets': 150,
            'total_alerts': 25,
            'average_uptime': 99.5,
            'maintenance_compliance': 92.3,
        },
        'recommendations': [
            'Optimize energy consumption',
            'Schedule preventive maintenance',
            'Update security policies',
        ],
    }

    # ---- Persist result ----
    report.status = 'completed'
    report.generated_at = timezone.now()
    report.save(update_fields=['status', 'generated_at'])

    return str(report.id)


# ============================
# DAILY KPI CALCULATION
# ============================
@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=30, retry_kwargs={'max_retries': 3})
def calculate_daily_kpis(self):
    """
    Calculate daily KPI values (idempotent)
    """
    yesterday = timezone.now() - timedelta(days=1)
    period_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    period_end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)

    for org in Organization.objects.all():
        kpis = KPI.objects.filter(organization=org, is_active=True)

        for kpi in kpis:
            value = _calculate_kpi_for_period(kpi, period_start, period_end)

            KPIValue.objects.update_or_create(
                kpi=kpi,
                period_start=period_start,
                period_end=period_end,
                defaults={
                    'value': value,
                    'metadata': {
                        'calculation_method': kpi.calculation_method,
                        'auto_generated': True,
                    },
                },
            )


# ============================
# KPI CALCULATION LOGIC
# ============================
def _calculate_kpi_for_period(kpi, period_start, period_end):
    """
    Placeholder KPI calculation logic.
    Replace with real analytics later.
    """
    if kpi.calculation_method == 'average':
        return 85.5
    if kpi.calculation_method == 'sum':
        return 1250.75
    if kpi.calculation_method == 'count':
        return 42
    if kpi.calculation_method == 'percentage':
        return 92.3
    return 0.0
