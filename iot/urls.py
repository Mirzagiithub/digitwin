from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TelemetryDataViewSet,
    AlertViewSet,
    DeviceViewSet,
    SensorViewSet,
    CommandViewSet,telemetry_view,alerts_view,
)

app_name = 'iot'

router = DefaultRouter()
router.register(r'telemetry', TelemetryDataViewSet, basename='telemetry')
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'devices', DeviceViewSet, basename='device')
router.register(r'sensors', SensorViewSet, basename='sensor')
router.register(r'commands', CommandViewSet, basename='command')

urlpatterns = [
    path('', include(router.urls)),
    path("telemetry/", telemetry_view, name="telemetry"),
    path("alerts/", alerts_view, name="alerts"),
]
