from django.contrib import admin
from .models import AssetHealth, PerformanceMetric, KPI, KPIValue, Report


# ============================
# BASE ORG-SCOPED ADMIN
# ============================
class OrganizationScopedAdmin(admin.ModelAdmin):
    """
    Restrict data visibility by organization for non-superusers
    """

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'organization') and request.user.organization:
            return qs.filter(organization=request.user.organization)
        return qs.none()


# ============================
# ASSET HEALTH
# ============================
@admin.register(AssetHealth)
class AssetHealthAdmin(admin.ModelAdmin):
    list_display = ('asset', 'score', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('asset__name',)
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    list_select_related = ('asset',)


# ============================
# PERFORMANCE METRIC
# ============================
@admin.register(PerformanceMetric)
class PerformanceMetricAdmin(admin.ModelAdmin):
    list_display = ('asset', 'metric_name', 'value', 'unit', 'timestamp', 'period')
    list_filter = ('metric_name', 'period', 'timestamp')
    search_fields = ('asset__name', 'metric_name')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    list_select_related = ('asset',)


# ============================
# KPI
# ============================
@admin.register(KPI)
class KPIAdmin(OrganizationScopedAdmin):
    list_display = ('name', 'organization', 'category', 'calculation_method', 'is_active')
    list_filter = ('category', 'calculation_method', 'is_active')
    search_fields = ('name', 'description', 'organization__name')
    ordering = ('name',)
    autocomplete_fields = ('organization',)


# ============================
# KPI VALUE
# ============================
@admin.register(KPIValue)
class KPIValueAdmin(OrganizationScopedAdmin):
    list_display = ('kpi', 'value', 'period_start', 'period_end', 'calculated_at')
    list_filter = ('period_start', 'period_end')
    search_fields = ('kpi__name',)
    readonly_fields = ('value', 'calculated_at')
    ordering = ('-period_start',)
    autocomplete_fields = ('kpi',)


# ============================
# REPORT
# ============================
@admin.register(Report)
class ReportAdmin(OrganizationScopedAdmin):
    list_display = (
        'name',
        'organization',
        'report_type',
        'format',
        'status',
        'created_at',
    )
    list_filter = ('report_type', 'format', 'status', 'created_at')
    search_fields = ('name', 'organization__name')
    readonly_fields = ('created_at', 'generated_at')
    ordering = ('-created_at',)
    autocomplete_fields = ('organization',)
