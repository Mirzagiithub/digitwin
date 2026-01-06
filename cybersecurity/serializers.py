from rest_framework import serializers
from .models import (
    SecurityDigitalTwin,
    ZeroTrustPolicy,
    ThreatDetectionRule,
    ThreatDetectionEvent,
    AttackCampaign,
)


# ============================
# SECURITY DIGITAL TWIN
# ============================
class SecurityDigitalTwinSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    asset_type = serializers.CharField(source='asset.asset_type.name', read_only=True)

    class Meta:
        model = SecurityDigitalTwin
        fields = [
            'id',
            'asset',
            'asset_name',
            'asset_type',
            'twin_type',
            'security_score',
            'risk_level',
            'zero_trust_status',
            'security_controls',
            'compliance_status',
            'behavioral_baseline',
            'baseline_established',
            'baseline_confidence',
            'threat_indicators',
            'active_threats',
            'last_security_scan',
            'last_sync',
            'sync_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'security_score',
            'risk_level',
            'created_at',
            'updated_at',
        ]

    def create(self, validated_data):
        request = self.context['request']
        validated_data['organization'] = request.user.organization
        return super().create(validated_data)


# ============================
# ZERO TRUST POLICY
# ============================
class ZeroTrustPolicySerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source='organization.name', read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.full_name', read_only=True
    )

    class Meta:
        model = ZeroTrustPolicy
        fields = [
            'id',
            'name',
            'description',
            'organization',
            'organization_name',
            'assets',
            'framework',
            'enforcement_mode',
            'is_active',
            'enforcement_status',
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

    def create(self, validated_data):
        request = self.context['request']
        validated_data['organization'] = request.user.organization
        validated_data['created_by'] = request.user
        return super().create(validated_data)


# ============================
# THREAT DETECTION RULE
# ============================
class ThreatDetectionRuleSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source='created_by.full_name', read_only=True
    )

    class Meta:
        model = ThreatDetectionRule
        fields = [
            'id',
            'name',
            'description',
            'rule_type',
            'detection_logic',
            'severity',
            'confidence',
            'is_active',
            'detection_count',
            'false_positive_count',
            'last_triggered',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'detection_count',
            'false_positive_count',
            'last_triggered',
            'created_at',
            'updated_at',
        ]

    def create(self, validated_data):
        request = self.context['request']
        validated_data['organization'] = request.user.organization
        validated_data['created_by'] = request.user
        return super().create(validated_data)


# ============================
# THREAT DETECTION EVENT
# ============================
class ThreatDetectionEventSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    asset_name = serializers.CharField(source='asset.name', read_only=True)

    class Meta:
        model = ThreatDetectionEvent
        fields = [
            'id',
            'rule',
            'rule_name',
            'asset',
            'asset_name',
            'timestamp',
            'telemetry_data',
            'severity',
            'confidence',
            'response_status',
            'investigated',
            'created_at',
        ]
        read_only_fields = ['id', 'timestamp', 'created_at']

    def create(self, validated_data):
        request = self.context['request']
        validated_data['organization'] = request.user.organization
        return super().create(validated_data)


# ============================
# ATTACK CAMPAIGN
# ============================
class AttackCampaignSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source='organization.name', read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.full_name', read_only=True
    )

    class Meta:
        model = AttackCampaign
        fields = [
            'id',
            'name',
            'description',
            'organization',
            'organization_name',
            'campaign_type',
            'status',
            'target_assets',
            'scheduled_start',
            'scheduled_end',
            'created_by',
            'created_by_name',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'organization',
            'created_by',
            'created_at',
        ]

    def validate(self, data):
        if data['scheduled_end'] <= data['scheduled_start']:
            raise serializers.ValidationError(
                'scheduled_end must be after scheduled_start'
            )
        return data

    def create(self, validated_data):
        request = self.context['request']
        validated_data['organization'] = request.user.organization
        validated_data['created_by'] = request.user
        return super().create(validated_data)
