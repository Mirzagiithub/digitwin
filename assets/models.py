from django.db import models
import uuid

from core.models import Organization, CustomUser


# ============================
# ASSET TYPE
# ============================
class AssetType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=50,
        choices=[
            ('mechanical', 'Mechanical'),
            ('electrical', 'Electrical'),
            ('electronic', 'Electronic'),
            ('software', 'Software'),
            ('infrastructure', 'Infrastructure'),
            ('other', 'Other'),
        ],
    )
    description = models.TextField(blank=True)
    specifications = models.JSONField(default=dict)
    image = models.ImageField(upload_to='asset_types/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'asset_types'
        ordering = ['name']
        verbose_name = 'Asset Type'
        verbose_name_plural = 'Asset Types'

    def __str__(self):
        return self.name


# ============================
# ASSET
# ============================
class Asset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    asset_id = models.CharField(max_length=100)
    name = models.CharField(max_length=200)

    asset_type = models.ForeignKey(
        AssetType,
        on_delete=models.PROTECT,
        related_name='assets',
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='assets',
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )

    location = models.CharField(max_length=500, blank=True)
    coordinates = models.JSONField(null=True, blank=True)

    STATUS_CHOICES = [
        ('operational', 'Operational'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
        ('maintenance', 'Under Maintenance'),
        ('offline', 'Offline'),
        ('decommissioned', 'Decommissioned'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='operational')

    manufacturer = models.CharField(max_length=200, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)

    installation_date = models.DateField(null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    expected_lifecycle = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Expected lifecycle in months',
    )

    current_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    depreciation_rate = models.FloatField(default=0.0)

    specifications = models.JSONField(default=dict)
    custom_fields = models.JSONField(default=dict)

    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_assets',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assets'
        ordering = ['-created_at']
        verbose_name = 'Asset'
        verbose_name_plural = 'Assets'
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'asset_id'],
                name='unique_asset_id_per_org',
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['asset_type', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.asset_id} - {self.name}'

    def clean(self):
        # Prevent cross-organization parent linking
        if self.parent and self.parent.organization_id != self.organization_id:
            raise ValueError('Parent asset must belong to the same organization')

    @property
    def health_score(self):
        """
        Lazy & safe integration with analytics app (optional).
        """
        try:
            from analytics.models import AssetHealth  # optional app
            health = (
                AssetHealth.objects
                .filter(asset=self)
                .order_by('-timestamp')
                .first()
            )
            return health.score if health else 0.0
        except Exception:
            return 0.0


# ============================
# ASSET METRIC
# ============================
class AssetMetric(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='metrics',
    )

    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)

    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)

    threshold_warning = models.FloatField(null=True, blank=True)
    threshold_critical = models.FloatField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'asset_metrics'
        verbose_name = 'Asset Metric'
        verbose_name_plural = 'Asset Metrics'
        constraints = [
            models.UniqueConstraint(
                fields=['asset', 'name'],
                name='unique_metric_per_asset',
            ),
        ]

    def __str__(self):
        return f'{self.asset.asset_id} - {self.name}'


# ============================
# ASSET RELATIONSHIP
# ============================
class AssetRelationship(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    parent_asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='parent_relationships',
    )
    child_asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='child_relationships',
    )

    relationship_type = models.CharField(
        max_length=50,
        choices=[
            ('part_of', 'Part Of'),
            ('connected_to', 'Connected To'),
            ('depends_on', 'Depends On'),
            ('feeds', 'Feeds Into'),
            ('controls', 'Controls'),
            ('monitors', 'Monitors'),
        ],
    )

    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'asset_relationships'
        verbose_name = 'Asset Relationship'
        verbose_name_plural = 'Asset Relationships'
        constraints = [
            models.UniqueConstraint(
                fields=['parent_asset', 'child_asset', 'relationship_type'],
                name='unique_asset_relationship',
            ),
        ]

    def clean(self):
        # Prevent cross-organization relationships
        if (
            self.parent_asset.organization_id
            != self.child_asset.organization_id
        ):
            raise ValueError('Assets must belong to the same organization')

    def __str__(self):
        return f'{self.parent_asset} → {self.child_asset} ({self.relationship_type})'
