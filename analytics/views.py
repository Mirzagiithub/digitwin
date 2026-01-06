from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Avg, Max, Min, Q, F
from django.db.models.functions import TruncDate, TruncHour, TruncMonth
from django.core.cache import cache
from datetime import datetime, timedelta

from .models import AssetHealth, PerformanceMetric, KPI, KPIValue, Report
from .serializers import (
    AssetHealthSerializer, PerformanceMetricSerializer,
    KPISerializer, KPIValueSerializer, ReportSerializer
)
from core.permissions import CanViewAnalytics, CanEditAssets
from assets.models import Asset
from iot.models import TelemetryData, Alert

class AssetHealthViewSet(viewsets.ModelViewSet):
    serializer_class = AssetHealthSerializer
    permission_classes = [IsAuthenticated, CanViewAnalytics]
    
    def get_queryset(self):
        user = self.request.user
        return AssetHealth.objects.filter(
            asset__organization=user.organization
        ).select_related('asset')
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        asset_id = request.query_params.get('asset_id')
        
        queryset = self.get_queryset()
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)
        
        queryset = queryset.order_by('-timestamp')[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        asset_id = request.data.get('asset_id')
        if not asset_id:
            return Response({'error': 'Asset ID is required'}, status=400)
        
        try:
            asset = Asset.objects.get(id=asset_id, organization=request.user.organization)
            
            # Calculate health score based on various factors
            health_score = self._calculate_asset_health(asset)
            
            # Create health record
            health_record = AssetHealth.objects.create(
                asset=asset,
                score=health_score,
                factors=self._get_health_factors(asset),
                recommendations=self._get_recommendations(asset, health_score)
            )
            
            serializer = self.get_serializer(health_record)
            return Response(serializer.data)
        
        except Asset.DoesNotExist:
            return Response({'error': 'Asset not found'}, status=404)
    
    def _calculate_asset_health(self, asset):
        # Simplified health calculation
        score = 100.0
        
        # Deduct for alerts
        recent_alerts = Alert.objects.filter(
            asset=asset,
            created_at__gte=timezone.now() - timedelta(days=7)
        )
        if recent_alerts.filter(severity='critical').exists():
            score -= 30
        elif recent_alerts.filter(severity='error').exists():
            score -= 20
        elif recent_alerts.filter(severity='warning').exists():
            score -= 10
        
        # Deduct for telemetry anomalies
        recent_telemetry = TelemetryData.objects.filter(
            asset=asset,
            timestamp__gte=timezone.now() - timedelta(hours=24)
        )
        if recent_telemetry.count() > 0:
            # Check for any telemetry values outside normal range
            # This is simplified - in production, you'd have proper anomaly detection
            pass
        
        return max(0.0, min(100.0, score))
    
    def _get_health_factors(self, asset):
        factors = {
            'asset_status': asset.status,
            'recent_alerts': Alert.objects.filter(
                asset=asset,
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'telemetry_quality': 0.95,  # Placeholder
            'maintenance_status': 'good',  # Placeholder
        }
        return factors
    
    def _get_recommendations(self, asset, health_score):
        recommendations = []
        
        if health_score < 70:
            recommendations.append('Schedule maintenance check')
        if health_score < 50:
            recommendations.append('Consider asset replacement')
        if asset.status == 'warning':
            recommendations.append('Investigate warning status')
        
        return recommendations

class PerformanceMetricViewSet(viewsets.ModelViewSet):
    serializer_class = PerformanceMetricSerializer
    permission_classes = [IsAuthenticated, CanViewAnalytics]
    
    def get_queryset(self):
        user = self.request.user
        return PerformanceMetric.objects.filter(
            asset__organization=user.organization
        ).select_related('asset')

class KPIViewSet(viewsets.ModelViewSet):
    serializer_class = KPISerializer
    permission_classes = [IsAuthenticated, CanEditAssets]
    
    def get_queryset(self):
        user = self.request.user
        return KPI.objects.filter(
            organization=user.organization
        ).select_related('organization')
    
    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)
    
    @action(detail=True, methods=['post'])
    def calculate(self, request, pk=None):
        kpi = self.get_object()
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end', timezone.now())
        
        if not period_start:
            # Default to last 24 hours
            period_start = timezone.now() - timedelta(days=1)
        
        # Calculate KPI value based on type
        value = self._calculate_kpi_value(kpi, period_start, period_end)
        
        # Create KPI value record
        kpi_value = KPIValue.objects.create(
            kpi=kpi,
            period_start=period_start,
            period_end=period_end,
            value=value,
            metadata={'calculation_method': kpi.calculation_method}
        )
        
        serializer = KPIValueSerializer(kpi_value)
        return Response(serializer.data)
    
    def _calculate_kpi_value(self, kpi, period_start, period_end):
        # Simplified KPI calculation
        # In production, you'd have proper calculation based on KPI type
        
        if kpi.calculation_method == 'average':
            # Calculate average of relevant metrics
            return 85.5  # Placeholder
        elif kpi.calculation_method == 'sum':
            # Calculate sum of relevant metrics
            return 1250.75  # Placeholder
        elif kpi.calculation_method == 'count':
            # Count relevant events
            return 42  # Placeholder
        else:
            return 0.0

class KPIValueViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = KPIValueSerializer
    permission_classes = [IsAuthenticated, CanViewAnalytics]
    
    def get_queryset(self):
        user = self.request.user
        return KPIValue.objects.filter(
            kpi__organization=user.organization
        ).select_related('kpi')

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, CanEditAssets]
    
    def get_queryset(self):
        user = self.request.user
        return Report.objects.filter(
            organization=user.organization
        ).select_related('organization', 'generated_by')
    
    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.user.organization,
            generated_by=self.request.user,
            status='pending'
        )
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        report = self.get_object()
        
        if report.status == 'generating':
            return Response({'error': 'Report is already being generated'}, status=400)
        
        report.status = 'generating'
        report.save()
        
        # Trigger report generation task
        from .tasks import generate_report_task
        generate_report_task.delay(str(report.id))
        
        return Response({'status': 'Report generation started', 'report_id': str(report.id)})

class AnalyticsDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, CanViewAnalytics]
    
    def get(self, request):
        organization = request.user.organization
        time_range = request.query_params.get('time_range', '24h')
        
        data = {
            'asset_health': self._get_asset_health_summary(organization),
            'kpi_summary': self._get_kpi_summary(organization),
            'performance_metrics': self._get_performance_metrics(organization, time_range),
            'alerts_summary': self._get_alerts_summary(organization, time_range),
        }
        
        return Response(data)
    
    def _get_asset_health_summary(self, organization):
        assets = Asset.objects.filter(organization=organization)
        health_records = AssetHealth.objects.filter(
            asset__organization=organization
        ).order_by('-timestamp')
        
        latest_health = {}
        for record in health_records:
            if record.asset_id not in latest_health:
                latest_health[record.asset_id] = record
        
        health_scores = [record.score for record in latest_health.values()]
        
        return {
            'total_assets': assets.count(),
            'assets_with_health': len(latest_health),
            'average_health': sum(health_scores) / len(health_scores) if health_scores else 0,
            'health_distribution': self._categorize_health_scores(health_scores)
        }
    
    def _categorize_health_scores(self, scores):
        categories = {
            'excellent': 0,  # 90-100
            'good': 0,       # 70-89
            'fair': 0,       # 50-69
            'poor': 0,       # 0-49
        }
        
        for score in scores:
            if score >= 90:
                categories['excellent'] += 1
            elif score >= 70:
                categories['good'] += 1
            elif score >= 50:
                categories['fair'] += 1
            else:
                categories['poor'] += 1
        
        return categories
    
    def _get_kpi_summary(self, organization):
        kpis = KPI.objects.filter(organization=organization, is_active=True)
        kpi_values = KPIValue.objects.filter(
            kpi__organization=organization,
            period_end__gte=timezone.now() - timedelta(days=30)
        ).select_related('kpi')
        
        summary = []
        for kpi in kpis:
            latest_value = kpi_values.filter(kpi=kpi).order_by('-period_end').first()
            summary.append({
                'kpi_id': str(kpi.id),
                'kpi_name': kpi.name,
                'category': kpi.category,
                'latest_value': latest_value.value if latest_value else None,
                'target_value': kpi.target_value,
                'unit': kpi.unit
            })
        
        return summary
    
    def _get_performance_metrics(self, organization, time_range):
        time_filter = self._get_time_filter(time_range)
        
        metrics = PerformanceMetric.objects.filter(
            asset__organization=organization,
            timestamp__gte=time_filter
        ).values('metric_name').annotate(
            avg_value=Avg('value'),
            min_value=Min('value'),
            max_value=Max('value'),
            count=Count('id')
        ).order_by('-count')[:10]
        
        return list(metrics)
    
    def _get_alerts_summary(self, organization, time_range):
        time_filter = self._get_time_filter(time_range)
        
        alerts = Alert.objects.filter(
            asset__organization=organization,
            created_at__gte=time_filter
        )
        
        return {
            'total': alerts.count(),
            'by_severity': list(alerts.values('severity').annotate(count=Count('id'))),
            'unacknowledged': alerts.filter(acknowledged=False).count(),
            'unresolved': alerts.filter(resolved=False).count(),
        }
    
    def _get_time_filter(self, time_range):
        now = timezone.now()
        if time_range == '1h':
            return now - timedelta(hours=1)
        elif time_range == '6h':
            return now - timedelta(hours=6)
        elif time_range == '24h':
            return now - timedelta(days=1)
        elif time_range == '7d':
            return now - timedelta(days=7)
        elif time_range == '30d':
            return now - timedelta(days=30)
        else:
            return now - timedelta(days=1)
        

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import KPI

@login_required
def kpi_list(request):
    return render(request, "analytics/kpis.html", {
        "kpis": KPI.objects.all()
    })
