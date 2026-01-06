from rest_framework import serializers
from .models import (
    SimulationScenario,
    SimulationResult,
    DigitalTwin,
    PredictiveModel,
    Prediction
)
from assets.serializers import AssetSerializer


# -----------------------------
# Simulation Scenario
# -----------------------------
class SimulationScenarioSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source='organization.name',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    target_assets_data = AssetSerializer(
        source='target_assets',
        many=True,
        read_only=True
    )

    class Meta:
        model = SimulationScenario
        fields = [
            'id',
            'name',
            'description',
            'organization',
            'organization_name',
            'scenario_type',
            'target_assets',
            'target_assets_data',
            'parameters',
            'initial_conditions',
            'constraints',
            'status',
            'scheduled_start',
            'actual_start',
            'actual_end',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'organization',
            'created_by',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        """
        Prevent invalid timeline states
        """
        scheduled = attrs.get('scheduled_start')
        actual_start = attrs.get('actual_start')
        actual_end = attrs.get('actual_end')

        if actual_start and scheduled and actual_start < scheduled:
            raise serializers.ValidationError(
                "Actual start cannot be before scheduled start."
            )

        if actual_end and actual_start and actual_end < actual_start:
            raise serializers.ValidationError(
                "Actual end cannot be before actual start."
            )

        return attrs


# -----------------------------
# Simulation Result
# -----------------------------
class SimulationResultSerializer(serializers.ModelSerializer):
    scenario_name = serializers.CharField(
        source='scenario.name',
        read_only=True
    )

    class Meta:
        model = SimulationResult
        fields = [
            'id',
            'scenario',
            'scenario_name',
            'metrics',
            'time_series_data',
            'snapshots',
            'events',
            'conclusions',
            'recommendations',
            'risk_assessment',
            'execution_time',
            'memory_usage',
            'generated_at',
        ]
        read_only_fields = [
            'id',
            'generated_at',
        ]


# -----------------------------
# Digital Twin
# -----------------------------
class DigitalTwinSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(
        source='asset.name',
        read_only=True
    )
    asset_type = serializers.CharField(
        source='asset.asset_type.name',
        read_only=True
    )

    class Meta:
        model = DigitalTwin
        fields = [
            'id',
            'asset',
            'asset_name',
            'asset_type',
            'twin_type',
            'model_file',
            'model_parameters',
            'model_version',
            'current_state',
            'historical_states',
            'accuracy',
            'last_calibrated',
            'is_active',
            'sync_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]

    def validate_accuracy(self, value):
        if value is not None and not (0 <= value <= 100):
            raise serializers.ValidationError(
                "Accuracy must be between 0 and 100."
            )
        return value


# -----------------------------
# Predictive Model
# -----------------------------
class PredictiveModelSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source='organization.name',
        read_only=True
    )

    class Meta:
        model = PredictiveModel
        fields = [
            'id',
            'name',
            'description',
            'organization',
            'organization_name',
            'model_type',
            'algorithm',
            'model_file',
            'hyperparameters',
            'feature_list',
            'training_data_size',
            'training_duration',
            'trained_at',
            'accuracy',
            'precision',
            'recall',
            'f1_score',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'organization',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        """
        Enforce ML metric sanity
        """
        for field in ['accuracy', 'precision', 'recall', 'f1_score']:
            value = attrs.get(field)
            if value is not None and not (0 <= value <= 1):
                raise serializers.ValidationError({
                    field: "Metric must be between 0 and 1."
                })
        return attrs


# -----------------------------
# Prediction
# -----------------------------
class PredictionSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(
        source='model.name',
        read_only=True
    )
    asset_name = serializers.CharField(
        source='asset.name',
        read_only=True
    )

    class Meta:
        model = Prediction
        fields = [
            'id',
            'model',
            'model_name',
            'asset',
            'asset_name',
            'input_features',
            'prediction_value',
            'confidence',
            'actual_value',
            'timestamp',
            'metadata',
        ]
        read_only_fields = [
            'id',
            'timestamp',
        ]

    def validate_confidence(self, value):
        if not (0 <= value <= 1):
            raise serializers.ValidationError(
                "Confidence must be between 0 and 1."
            )
        return value
