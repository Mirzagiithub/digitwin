from django.contrib import admin
from .models import (
    SimulationScenario,
    SimulationResult,
    DigitalTwin,
    PredictiveModel,
    Prediction
)


@admin.register(SimulationScenario)
class SimulationScenarioAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'organization',
        'scenario_type',
        'status',
        'created_by',
        'created_at',
    )
    list_filter = (
        'scenario_type',
        'status',
        'created_at',
    )
    search_fields = (
        'name',
        'description',
        'organization__name',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    filter_horizontal = ('target_assets',)
    list_select_related = ('organization', 'created_by')
    ordering = ('-created_at',)


@admin.register(SimulationResult)
class SimulationResultAdmin(admin.ModelAdmin):
    list_display = (
        'scenario',
        'execution_time',
        'generated_at',
    )
    list_filter = ('generated_at',)
    search_fields = (
        'scenario__name',
        'conclusions',
    )
    readonly_fields = ('generated_at',)
    list_select_related = ('scenario',)
    ordering = ('-generated_at',)


@admin.register(DigitalTwin)
class DigitalTwinAdmin(admin.ModelAdmin):
    list_display = (
        'asset',
        'twin_type',
        'model_version',
        'is_active',
        'sync_status',
        'updated_at',
    )
    list_filter = (
        'twin_type',
        'is_active',
        'sync_status',
    )
    search_fields = (
        'asset__name',
        'asset__asset_id',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    list_select_related = ('asset',)
    ordering = ('-updated_at',)


@admin.register(PredictiveModel)
class PredictiveModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'organization',
        'model_type',
        'algorithm',
        'status',
        'accuracy',
        'trained_at',
    )
    list_filter = (
        'model_type',
        'algorithm',
        'status',
    )
    search_fields = (
        'name',
        'description',
        'organization__name',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    list_select_related = ('organization',)
    ordering = ('-created_at',)


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = (
        'model',
        'asset',
        'prediction_value',
        'confidence',
        'timestamp',
    )
    list_filter = (
        'timestamp',
        'model__model_type',
    )
    search_fields = (
        'model__name',
        'asset__name',
    )
    readonly_fields = ('timestamp',)
    list_select_related = ('model', 'asset')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
