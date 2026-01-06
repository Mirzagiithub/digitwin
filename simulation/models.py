from django.db import models
import uuid
from django.utils import timezone

from core.models import Organization, CustomUser
from assets.models import Asset


# ==========================
# SIMULATION SCENARIOS
# ==========================
class SimulationScenario(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='simulation_scenarios'
    )

    SCENARIO_TYPES = [
        ('what_if', 'What-If Analysis'),
        ('failure', 'Failure Simulation'),
        ('optimization', 'Optimization'),
        ('load_test', 'Load Testing'),
        ('safety', 'Safety Analysis'),
        ('maintenance', 'Maintenance Planning'),
    ]
    scenario_type = models.CharField(max_length=50, choices=SCENARIO_TYPES)

    target_assets = models.ManyToManyField(
        Asset,
        related_name='simulation_targets'
    )

    parameters = models.JSONField(default=dict)
    initial_conditions = models.JSONField(default=dict)
    constraints = models.JSONField(default=dict)

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    scheduled_start = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_simulations'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'simulation_scenarios'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'scenario_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_scenario_type_display()})"


# ==========================
# SIMULATION RESULTS
# ==========================
class SimulationResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    scenario = models.ForeignKey(
        SimulationScenario,
        on_delete=models.CASCADE,
        related_name='results'
    )

    metrics = models.JSONField(default=dict)
    time_series_data = models.JSONField(default=dict, blank=True)
    snapshots = models.JSONField(default=list, blank=True)
    events = models.JSONField(default=list, blank=True)

    conclusions = models.TextField(blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    risk_assessment = models.JSONField(default=dict, blank=True)

    execution_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Execution time in seconds"
    )
    memory_usage = models.FloatField(
        null=True,
        blank=True,
        help_text="Memory usage in MB"
    )

    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'simulation_results'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['scenario', '-generated_at']),
        ]

    def __str__(self):
        return f"Results for {self.scenario.name}"


# ==========================
# DIGITAL TWIN
# ==========================
class DigitalTwin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name='digital_twin'
    )

    TWIN_TYPES = [
        ('physics_based', 'Physics-Based'),
        ('data_driven', 'Data-Driven'),
        ('hybrid', 'Hybrid'),
        ('behavioral', 'Behavioral'),
    ]
    twin_type = models.CharField(max_length=50, choices=TWIN_TYPES)

    model_file = models.FileField(
        upload_to='digital_twins/models/',
        null=True,
        blank=True
    )
    model_parameters = models.JSONField(default=dict)
    model_version = models.CharField(max_length=20, default='1.0.0')

    current_state = models.JSONField(default=dict)
    historical_states = models.JSONField(default=list, blank=True)

    accuracy = models.FloatField(null=True, blank=True)
    last_calibrated = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    sync_status = models.CharField(
        max_length=20,
        choices=[
            ('synced', 'Synced'),
            ('out_of_sync', 'Out of Sync'),
            ('error', 'Error'),
        ],
        default='synced'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'digital_twins'
        verbose_name = 'Digital Twin'
        verbose_name_plural = 'Digital Twins'

    def __str__(self):
        return f"Digital Twin: {self.asset.name}"


# ==========================
# PREDICTIVE MODELS
# ==========================
class PredictiveModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='predictive_models'
    )

    MODEL_TYPES = [
        ('anomaly_detection', 'Anomaly Detection'),
        ('predictive_maintenance', 'Predictive Maintenance'),
        ('failure_prediction', 'Failure Prediction'),
        ('performance_forecast', 'Performance Forecast'),
        ('lifetime_prediction', 'Lifetime Prediction'),
    ]
    model_type = models.CharField(max_length=50, choices=MODEL_TYPES)

    algorithm = models.CharField(max_length=100)
    model_file = models.FileField(upload_to='predictive_models/artifacts/')
    hyperparameters = models.JSONField(default=dict)
    feature_list = models.JSONField(default=list)

    training_data_size = models.IntegerField(default=0)
    training_duration = models.FloatField(null=True, blank=True)
    trained_at = models.DateTimeField(null=True, blank=True)

    accuracy = models.FloatField(null=True, blank=True)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ('training', 'Training'),
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('retired', 'Retired'),
        ],
        default='training'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'predictive_models'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_model_type_display()})"


# ==========================
# PREDICTIONS
# ==========================
class Prediction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    model = models.ForeignKey(
        PredictiveModel,
        on_delete=models.CASCADE,
        related_name='predictions'
    )
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='predictions'
    )

    input_features = models.JSONField(default=dict)
    prediction_value = models.FloatField()
    confidence = models.FloatField()

    actual_value = models.FloatField(null=True, blank=True)

    timestamp = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'predictions'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['asset', '-timestamp']),
            models.Index(fields=['model', '-timestamp']),
        ]

    def __str__(self):
        return f"Prediction by {self.model.name} for {self.asset.name}"
