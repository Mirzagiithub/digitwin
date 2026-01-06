from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AssetHealthViewSet,
    PerformanceMetricViewSet,
    KPIViewSet,
    KPIValueViewSet,
    ReportViewSet,
    AnalyticsDashboardView,kpi_list,
)

app_name = 'analytics'

router = DefaultRouter()
router.register(r'asset-health', AssetHealthViewSet, basename='asset-health')
router.register(r'performance-metrics', PerformanceMetricViewSet, basename='performance-metric')
router.register(r'kpis', KPIViewSet, basename='kpi')
router.register(r'kpi-values', KPIValueViewSet, basename='kpi-value')
router.register(r'reports', ReportViewSet, basename='report')

urlpatterns = [
    path('dashboard/', AnalyticsDashboardView.as_view(), name='analytics-dashboard'),
    path('', include(router.urls)),
     path("kpis/", kpi_list, name="kpi-list"),
]
