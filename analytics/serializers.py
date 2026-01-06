from rest_framework import serializers
from .models import AssetHealth, PerformanceMetric, KPI, KPIValue, Report


# ============================
# ASSET HEALTH
# ============================
class AssetHealthSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(
        source='asset.name', read_only=True
    )

    class Meta:
        model = AssetHealth
        fields = [
            'id',
            'asset',
            'asset_name',
            'score',
            'factors',
            'recommendations',
            'timestamp',
        ]
        read_only_fields = ['id', 'timestamp']

    def create(self, validated_data):
        request = self.context['request']
        validated_data['organization'] = request.user.organization
        return super().create(validated_data)


# ============================
# PERFORMANCE METRIC
# ============================
class PerformanceMetricSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(
        source='asset.name', read_only=True
    )

    class Meta:
        model = PerformanceMetric
        fields = [
            'id',
            'asset',
            'asset_name',
            'metric_name',
            'value',
            'target',
            'unit',
            'timestamp',
            'period',
        ]
        read_only_fields = ['id', 'timestamp']

    def create(self, validated_data):
        request = self.context['request']
        validated_data['organization'] = request.user.organization
        return super().create(validated_data)


# ============================
# KPI
# ============================
class KPISerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source='organization.name', read_only=True
    )

    class Meta:
        model = KPI
        fields = [
            'id',
            'name',
            'description',
            'organization',
            'organization_name',
            'category',
            'calculation_method',
            'target_value',
            'warning_threshold',
            'critical_threshold',
            'unit',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'organization',
            'created_at',
            'updated_at',
        ]

    def validate(self, data):
        target = data.get('target_value')
        warning = data.get('warning_threshold')
        critical = data.get('critical_threshold')

        if critical is not None and warning is not None and critical > warning:
            raise serializers.ValidationError(
                'Critical threshold must be less than or equal to warning threshold'
            )

        if warning is not None and target is not None and warning > target:
            raise serializers.ValidationError(
                'Warning threshold must be less than or equal to target value'
            )

        return data

    def create(self, validated_data):
        request = self.context['request']
        validated_data['organization'] = request.user.organization
        return super().create(validated_data)


# ============================
# KPI VALUE
# ============================
class KPIValueSerializer(serializers.ModelSerializer):
    kpi_name = serializers.CharField(
        source='kpi.name', read_only=True
    )

    class Meta:
        model = KPIValue
        fields = [
            'id',
            'kpi',
            'kpi_name',
            'period_start',
            'period_end',
            'value',
            'calculated_at',
            'metadata',
        ]
        read_only_fields = ['id', 'calculated_at']


# ============================
# REPORT
# ============================
class ReportSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source='organization.name', read_only=True
    )
    generated_by_name = serializers.CharField(
        source='generated_by.full_name', read_only=True
    )

    class Meta:
        model = Report
        fields = [
            'id',
            'name',
            'organization',
            'organization_name',
            'report_type',
            'format',
            'parameters',
            'status',
            'file',
            'generated_by',
            'generated_by_name',
            'generated_at',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'organization',
            'generated_by',
            'created_at',
            'generated_at',
        ]

    def create(self, validated_data):
        request = self.context['request']
        validated_data['organization'] = request.user.organization
        validated_data['generated_by'] = request.user
        return super().create(validated_data)
