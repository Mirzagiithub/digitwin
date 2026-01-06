from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from django.utils import timezone
from django.db.models import Count, Avg, Max, Min, Q
from datetime import timedelta

from .models import TelemetryData, Alert, Device, Sensor, Command
from .serializers import (
    TelemetryDataSerializer,
    AlertSerializer,
    DeviceSerializer,
    SensorSerializer,
    CommandSerializer,
)
from core.permissions import CanViewAnalytics, CanEditAssets


# -------------------------------------------------------------------
# Helper: centralized time filter (NO duplication)
# -------------------------------------------------------------------
def get_time_filter(time_range: str):
    now = timezone.now()
    mapping = {
        '1h': timedelta(hours=1),
        '6h': timedelta(hours=6),
        '12h': timedelta(hours=12),
        '24h': timedelta(days=1),
        '7d': timedelta(days=7),
        '30d': timedelta(days=30),
    }
    return now - mapping.get(time_range, timedelta(days=1))


# -------------------------------------------------------------------
# Telemetry (READ-ONLY — ingest happens elsewhere)
# -------------------------------------------------------------------
class TelemetryDataViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TelemetryDataSerializer
    permission_classes = [IsAuthenticated, CanViewAnalytics]

    def get_queryset(self):
        return TelemetryData.objects.filter(
            asset__organization=self.request.user.organization
        ).select_related('asset')

    @action(detail=False, methods=['get'])
    def latest(self, request):
        asset_id = request.query_params.get('asset_id')
        metric = request.query_params.get('metric')
        limit = min(int(request.query_params.get('limit', 100)), 500)

        queryset = self.get_queryset()

        if asset_id:
            queryset = queryset.filter(asset__id=asset_id)
        if metric:
            queryset = queryset.filter(metric=metric)

        queryset = queryset.order_by('-timestamp')[:limit]
        return Response(self.get_serializer(queryset, many=True).data)

    @action(detail=False, methods=['get'])
    def metrics(self, request):
        metrics = (
            self.get_queryset()
            .values_list('metric', flat=True)
            .distinct()
        )
        return Response({'metrics': list(metrics)})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        asset_id = request.query_params.get('asset_id')
        metric = request.query_params.get('metric')
        time_range = request.query_params.get('time_range', '24h')

        queryset = self.get_queryset().filter(
            timestamp__gte=get_time_filter(time_range)
        )

        if asset_id:
            queryset = queryset.filter(asset__id=asset_id)
        if metric:
            queryset = queryset.filter(metric=metric)

        stats = queryset.aggregate(
            count=Count('id'),
            avg_value=Avg('value'),
            max_value=Max('value'),
            min_value=Min('value'),
            latest_timestamp=Max('timestamp'),
        )

        return Response(stats)


# -------------------------------------------------------------------
# Alerts (READ-ONLY + controlled actions)
# -------------------------------------------------------------------
class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated, CanViewAnalytics]

    def get_queryset(self):
        return Alert.objects.filter(
            asset__organization=self.request.user.organization
        ).select_related('asset', 'acknowledged_by', 'resolved_by')

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        alert = self.get_object()

        alert.acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save(update_fields=[
            'acknowledged', 'acknowledged_by', 'acknowledged_at'
        ])

        return Response({'status': 'acknowledged'})

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        alert = self.get_object()

        alert.resolved = True
        alert.resolved_by = request.user
        alert.resolved_at = timezone.now()
        alert.save(update_fields=[
            'resolved', 'resolved_by', 'resolved_at'
        ])

        return Response({'status': 'resolved'})

    @action(detail=False, methods=['get'])
    def summary(self, request):
        time_range = request.query_params.get('time_range', '24h')
        alerts = self.get_queryset().filter(
            created_at__gte=get_time_filter(time_range)
        )

        return Response({
            'summary': alerts.aggregate(
                total=Count('id'),
                unacknowledged=Count('id', filter=Q(acknowledged=False)),
                unresolved=Count('id', filter=Q(resolved=False)),
                critical=Count('id', filter=Q(severity='critical')),
            ),
            'severity_distribution': list(
                alerts.values('severity')
                .annotate(count=Count('id'))
                .order_by('-count')
            )
        })


# -------------------------------------------------------------------
# Devices
# -------------------------------------------------------------------
class DeviceViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated, CanEditAssets]

    def get_queryset(self):
        return Device.objects.filter(
            asset__organization=self.request.user.organization
        ).select_related('asset')

    @action(detail=True, methods=['post'])
    def send_command(self, request, pk=None):
        device = self.get_object()

        if device.asset.organization != request.user.organization:
            return Response({'error': 'Forbidden'}, status=403)

        command_type = request.data.get('command_type')
        if not command_type:
            return Response(
                {'error': 'command_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        command = Command.objects.create(
            device=device,
            command_type=command_type,
            payload=request.data.get('payload', {}),
            issued_by=request.user,
            status='sent',
        )

        return Response({
            'status': 'command_sent',
            'command_id': str(command.id)
        })

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        device = self.get_object()

        telemetry = TelemetryData.objects.filter(
            asset=device.asset
        ).order_by('-timestamp')[:10]

        alerts = Alert.objects.filter(
            asset=device.asset
        ).order_by('-created_at')[:5]

        return Response({
            'device': DeviceSerializer(device).data,
            'recent_telemetry': TelemetryDataSerializer(telemetry, many=True).data,
            'recent_alerts': AlertSerializer(alerts, many=True).data,
            'connection_status': device.connection_status,
            'last_seen': device.last_seen,
            'uptime': 99.5 if device.connection_status == 'connected' else 0.0,
        })


# -------------------------------------------------------------------
# Sensors
# -------------------------------------------------------------------
class SensorViewSet(viewsets.ModelViewSet):
    serializer_class = SensorSerializer
    permission_classes = [IsAuthenticated, CanViewAnalytics]

    def get_queryset(self):
        return Sensor.objects.filter(
            device__asset__organization=self.request.user.organization
        ).select_related('device', 'device__asset')

    @action(detail=True, methods=['get'])
    def telemetry(self, request, pk=None):
        sensor = self.get_object()
        time_range = request.query_params.get('time_range', '24h')

        telemetry = TelemetryData.objects.filter(
            asset=sensor.device.asset,
            metric=sensor.name,
            timestamp__gte=get_time_filter(time_range)
        ).order_by('timestamp')

        return Response(
            TelemetryDataSerializer(telemetry, many=True).data
        )


# -------------------------------------------------------------------
# Commands (READ-ONLY)
# -------------------------------------------------------------------
class CommandViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CommandSerializer
    permission_classes = [IsAuthenticated, CanEditAssets]

    def get_queryset(self):
        return Command.objects.filter(
            device__asset__organization=self.request.user.organization
        ).select_related('device', 'issued_by')


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import TelemetryData, Alert

@login_required
def telemetry_view(request):
    telemetry = TelemetryData.objects.order_by("-timestamp")[:100]
    return render(request, "iot/telemetry.html", {"telemetry": telemetry})

@login_required
def alerts_view(request):
    alerts = Alert.objects.order_by("-created_at")
    return render(request, "iot/alerts.html", {"alerts": alerts})
