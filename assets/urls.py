from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AssetTypeViewSet,
    AssetViewSet,
    AssetMetricViewSet,
    AssetRelationshipViewSet,
    asset_detail,asset_list,
)

app_name = 'assets'

router = DefaultRouter()
router.register(r'asset-types', AssetTypeViewSet, basename='asset-type')
router.register(r'assets', AssetViewSet, basename='asset')
router.register(r'asset-metrics', AssetMetricViewSet, basename='asset-metric')
router.register(r'asset-relationships', AssetRelationshipViewSet, basename='asset-relationship')

urlpatterns = [
    path('', include(router.urls)),
    path("", asset_list, name="asset-list"),
    path("<uuid:pk>/", asset_detail, name="asset-detail"),
]
