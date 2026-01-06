from django.db import models
from django.utils import timezone
import uuid

from core.models import Organization, CustomUser
from assets.models import Asset


# ============================
# ASSET HEALTH
# ============================
class AssetHealth(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='health_records',
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='asset_health',
    )

    score = models.FloatField(default=100.0)
    factors = models.JSONField(default=dict)
    recommendations = models.JSONField(default=list)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'asset_health'
        ordering = ['-timestamp']
        verbose_name = 'Asset Health'
        verbose_name_plural = 'Asset Health'
        indexes = [
            models.Index(fields=['asset', 'timestamp']),
            models.Index(fields=['organization', 'timestamp']),
        ]

    def __str__(self):
        return f'{self.asset.name} Health: {self.score}'


# ============================
# PERFORMANCE METRIC
# ============================
class PerformanceMetric(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='performance_metrics',
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='performance_metrics',
    )

    metric_name = models.CharField(max_length=100)
    value = models.FloatField()
    target = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)

    timestamp = models.DateTimeField(default=timezone.now)
    period = models.CharField(
        max_length=20,
        choices=[
            ('instant', 'Instant'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='instant',
    )

    class Meta:
        db_table = 'performance_metrics'
        ordering = ['-timestamp']
        verbose_name = 'Performance Metric'
        verbose_name_plural = 'Performance Metrics'
        indexes = [
            models.Index(fields=['asset', 'metric_name', 'timestamp']),
            models.Index(fields=['organization', 'timestamp']),
        ]

    def __str__(self):
        return f'{self.asset.name} - {self.metric_name}: {self.value}'


# ============================
# KPI
# ============================
class KPI(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='kpis',
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    category = models.CharField(
        max_length=100,
        choices=[
            ('operational', 'Operational'),
            ('financial', 'Financial'),
            ('quality', 'Quality'),
            ('safety', 'Safety'),
            ('environmental', 'Environmental'),
        ],
    )

    calculation_method = models.CharField(
        max_length=50,
        choices=[
            ('sum', 'Sum'),
            ('average', 'Average'),
            ('count', 'Count'),
            ('percentage', 'Percentage'),
            ('ratio', 'Ratio'),
        ],
    )

    target_value = models.FloatField(null=True, blank=True)
    warning_threshold = models.FloatField(null=True, blank=True)
    critical_threshold = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'kpis'
        ordering = ['category', 'name']
        verbose_name = 'KPI'
        verbose_name_plural = 'KPIs'
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'name'],
                name='unique_kpi_per_org',
            ),
        ]

    def clean(self):
        if (
            self.critical_threshold
            and self.warning_threshold
            and self.critical_threshold > self.warning_threshold
        ):
            raise ValueError('Critical threshold must be ≤ warning threshold')

        if (
            self.target_value
            and self.warning_threshold
            and self.warning_threshold > self.target_value
        ):
            raise ValueError('Warning threshold must be ≤ target value')

    def __str__(self):
        return f'{self.name} ({self.category})'


# ============================
# KPI VALUE
# ============================
class KPIValue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    kpi = models.ForeignKey(
        KPI,
        on_delete=models.CASCADE,
        related_name='values',
    )

    period_start = models.DateTimeField()
    period_end = models.DateTimeField()

    value = models.FloatField()
    calculated_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'kpi_values'
        ordering = ['-period_end']
        verbose_name = 'KPI Value'
        verbose_name_plural = 'KPI Values'
        constraints = [
            models.UniqueConstraint(
                fields=['kpi', 'period_start', 'period_end'],
                name='unique_kpi_value_period',
            ),
        ]
        indexes = [
            models.Index(fields=['kpi', 'period_end']),
        ]

    def __str__(self):
        return f'{self.kpi.name}: {self.value}'


# ============================
# REPORT
# ============================
class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='reports',
    )

    name = models.CharField(max_length=200)

    report_type = models.CharField(
        max_length=50,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('annual', 'Annual'),
            ('ad_hoc', 'Ad Hoc'),
        ],
    )

    format = models.CharField(
        max_length=20,
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel'),
            ('html', 'HTML'),
            ('json', 'JSON'),
        ],
        default='pdf',
    )

    parameters = models.JSONField(default=dict)

    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('generating', 'Generating'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending',
    )

    file = models.FileField(upload_to='reports/', null=True, blank=True)

    generated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_reports',
    )

    generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'

    def __str__(self):
        return f'{self.name} - {self.get_report_type_display()}'
