from rest_framework import serializers
from .models import AssetType, Asset, AssetMetric, AssetRelationship


# ============================
# ASSET TYPE
# ============================
class AssetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetType
        fields = [
            'id', 'name', 'category', 'description',
            'specifications', 'image',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================
# ASSET
# ============================
class AssetSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source='organization.name', read_only=True
    )
    asset_type_name = serializers.CharField(
        source='asset_type.name', read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.full_name', read_only=True
    )
    health_score = serializers.FloatField(read_only=True)

    class Meta:
        model = Asset
        fields = [
            'id',
            'asset_id',
            'name',
            'asset_type',
            'asset_type_name',
            'organization',
            'organization_name',
            'parent',
            'location',
            'coordinates',
            'status',
            'manufacturer',
            'model_number',
            'serial_number',
            'installation_date',
            'warranty_expiry',
            'expected_lifecycle',
            'current_value',
            'depreciation_rate',
            'specifications',
            'custom_fields',
            'created_by',
            'created_by_name',
            'health_score',
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

    def validate_asset_id(self, value):
        organization = self.context.get('organization')
        if not organization:
            return value.upper()

        qs = Asset.objects.filter(
            organization=organization,
            asset_id__iexact=value,
        )

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                'Asset ID already exists in this organization'
            )

        return value.upper()

    def validate_parent(self, parent):
        organization = self.context.get('organization')
        if parent and organization and parent.organization != organization:
            raise serializers.ValidationError(
                'Parent asset must belong to the same organization'
            )
        return parent

    def create(self, validated_data):
        request = self.context.get('request')
        organization = self.context.get('organization')

        validated_data['organization'] = organization
        validated_data['created_by'] = request.user

        return super().create(validated_data)


# ============================
# ASSET METRIC
# ============================
class AssetMetricSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(
        source='asset.name', read_only=True
    )

    class Meta:
        model = AssetMetric
        fields = [
            'id',
            'asset',
            'asset_name',
            'name',
            'unit',
            'min_value',
            'max_value',
            'threshold_warning',
            'threshold_critical',
            'is_active',
        ]
        read_only_fields = ['id']


# ============================
# ASSET RELATIONSHIP
# ============================
class AssetRelationshipSerializer(serializers.ModelSerializer):
    parent_asset_name = serializers.CharField(
        source='parent_asset.name', read_only=True
    )
    child_asset_name = serializers.CharField(
        source='child_asset.name', read_only=True
    )

    class Meta:
        model = AssetRelationship
        fields = [
            'id',
            'parent_asset',
            'parent_asset_name',
            'child_asset',
            'child_asset_name',
            'relationship_type',
            'description',
            'metadata',
        ]
        read_only_fields = ['id']

    def validate(self, data):
        parent = data.get('parent_asset')
        child = data.get('child_asset')

        if parent.organization_id != child.organization_id:
            raise serializers.ValidationError(
                'Assets must belong to the same organization'
            )

        return data
