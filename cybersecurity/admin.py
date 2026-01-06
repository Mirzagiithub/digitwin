from django.contrib import admin
from .models import (
    SecurityDigitalTwin,
    ZeroTrustPolicy,
    ThreatDetectionRule,
    ThreatDetectionEvent,
    AttackCampaign
)


@admin.register(SecurityDigitalTwin)
class SecurityDigitalTwinAdmin(admin.ModelAdmin):
    list_display = (
        'asset',
        'twin_type',
        'security_score',
        'risk_level',
        'zero_trust_status',
        'sync_status',
        'updated_at',
    )
    list_filter = ('risk_level', 'zero_trust_status', 'sync_status')
    search_fields = ('asset__name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ZeroTrustPolicy)
class ZeroTrustPolicyAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'organization',
        'framework',
        'enforcement_mode',
        'enforcement_status',
        'is_active',
        'created_at',
    )
    list_filter = ('framework', 'enforcement_mode', 'enforcement_status', 'is_active')
    search_fields = ('name', 'organization__name')
    filter_horizontal = ('assets',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ThreatDetectionRule)
class ThreatDetectionRuleAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'organization',
        'rule_type',
        'severity',
        'is_active',
        'detection_count',
        'false_positive_count',
        'created_at',
    )
    list_filter = ('rule_type', 'severity', 'is_active')
    search_fields = ('name',)
    readonly_fields = (
        'detection_count',
        'false_positive_count',
        'last_triggered',
        'created_at',
        'updated_at',
    )


@admin.register(ThreatDetectionEvent)
class ThreatDetectionEventAdmin(admin.ModelAdmin):
    list_display = (
        'rule',
        'asset',
        'severity',
        'confidence',
        'investigated',
        'timestamp',
    )
    list_filter = ('severity', 'investigated')
    search_fields = ('rule__name', 'asset__name')
    readonly_fields = ('timestamp', 'created_at')


@admin.register(AttackCampaign)
class AttackCampaignAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'organization',
        'campaign_type',
        'status',
        'scheduled_start',
        'scheduled_end',
    )
    list_filter = ('campaign_type', 'status')
    search_fields = ('name', 'organization__name')
    filter_horizontal = ('target_assets', 'target_users')
    readonly_fields = ('created_at',)
