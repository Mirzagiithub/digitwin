from django.contrib import admin
from .models import TelemetryData, Alert, Device, Sensor, Command


@admin.register(TelemetryData)
class TelemetryDataAdmin(admin.ModelAdmin):
    list_display = ('asset', 'metric', 'value', 'unit', 'timestamp')
    list_filter = ('metric', 'timestamp', 'asset')
    search_fields = ('asset__name', 'metric')
    readonly_fields = ('asset', 'metric', 'value', 'unit', 'timestamp')
    date_hierarchy = 'timestamp'
    list_select_related = ('asset',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'asset', 'severity', 'acknowledged', 'resolved', 'created_at')
    list_filter = ('severity', 'acknowledged', 'resolved', 'created_at')
    search_fields = ('title', 'message', 'asset__name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    list_select_related = ('asset',)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'asset', 'device_type', 'protocol', 'connection_status', 'last_seen')
    list_filter = ('device_type', 'protocol', 'connection_status')
    search_fields = ('device_id', 'asset__name', 'manufacturer', 'model')
    list_select_related = ('asset',)
    raw_id_fields = ('asset',)


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ('sensor_id', 'name', 'device', 'sensor_type', 'unit', 'is_active')
    list_filter = ('sensor_type', 'is_active')
    search_fields = ('sensor_id', 'name', 'device__device_id')
    list_select_related = ('device',)
    raw_id_fields = ('device',)


@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = ('command_type', 'device', 'issued_by', 'issued_at', 'status')
    list_filter = ('command_type', 'status', 'issued_at')
    search_fields = ('command_type', 'device__device_id')
    readonly_fields = ('issued_at', 'response_received_at')
    list_select_related = ('device', 'issued_by')
    raw_id_fields = ('device', 'issued_by')

    def has_add_permission(self, request):
        return False
