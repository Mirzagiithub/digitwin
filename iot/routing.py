from django.urls import re_path
from .consumers import TelemetryConsumer, AlertConsumer, AssetConsumer

websocket_urlpatterns = [
    re_path(r'^ws/iot/telemetry/$', TelemetryConsumer.as_asgi()),
    re_path(r'^ws/iot/alerts/$', AlertConsumer.as_asgi()),
    re_path(r'^ws/iot/assets/$', AssetConsumer.as_asgi()),
]
