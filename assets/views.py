from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q

from .models import AssetType, Asset, AssetMetric, AssetRelationship
from .serializers import (
    AssetTypeSerializer,
    AssetSerializer,
    AssetMetricSerializer,
    AssetRelationshipSerializer,
)
from core.permissions import CanEditAssets, CanViewAnalytics


# ============================
# ASSET TYPE
# ============================
class AssetTypeViewSet(viewsets.ModelViewSet):
    serializer_class = AssetTypeSerializer
    permission_classes = [IsAuthenticated, CanEditAssets]

    def get_queryset(self):
        return AssetType.objects.all().order_by('name')


# ============================
# ASSET
# ============================
class AssetViewSet(viewsets.ModelViewSet):
    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated, CanEditAssets]

    def get_queryset(self):
        return (
            Asset.objects
            .filter(organization=self.request.user.organization)
            .select_related('asset_type', 'organization', 'created_by')
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization'] = self.request.user.organization
        context['request'] = self.request
        return context

    # ----------------------------
    # RELATED DATA
    # ----------------------------
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def metrics(self, request, pk=None):
        asset = self.get_object()
        serializer = AssetMetricSerializer(asset.metrics.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def relationships(self, request, pk=None):
        asset = self.get_object()

        parents = AssetRelationship.objects.filter(parent_asset=asset)
        children = AssetRelationship.objects.filter(child_asset=asset)

        return Response({
            'parents': AssetRelationshipSerializer(parents, many=True).data,
            'children': AssetRelationshipSerializer(children, many=True).data,
        })

    # ----------------------------
    # ANALYTICS (OPTIONAL)
    # ----------------------------
    @action(
        detail=True,
        methods=['get'],
        permission_classes=[IsAuthenticated, CanViewAnalytics],
    )
    def status(self, request, pk=None):
        asset = self.get_object()

        health_score = asset.health_score

        return Response({
            'asset': AssetSerializer(asset, context=self.get_serializer_context()).data,
            'health_score': health_score,
        })

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated, CanViewAnalytics],
    )
    def summary(self, request):
        assets = self.get_queryset()

        summary = assets.aggregate(
            total=Count('id'),
            operational=Count('id', filter=Q(status='operational')),
            warning=Count('id', filter=Q(status='warning')),
            critical=Count('id', filter=Q(status='critical')),
            maintenance=Count('id', filter=Q(status='maintenance')),
            offline=Count('id', filter=Q(status='offline')),
        )

        type_distribution = list(
            assets.values('asset_type__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        recent_assets = list(
            assets.order_by('-created_at').values(
                'id',
                'name',
                'asset_type__name',
                'status',
                'created_at',
            )[:5]
        )

        return Response({
            'summary': summary,
            'type_distribution': type_distribution,
            'recent_assets': recent_assets,
        })


# ============================
# ASSET METRIC
# ============================
class AssetMetricViewSet(viewsets.ModelViewSet):
    serializer_class = AssetMetricSerializer
    permission_classes = [IsAuthenticated, CanEditAssets]

    def get_queryset(self):
        return AssetMetric.objects.filter(
            asset__organization=self.request.user.organization
        ).select_related('asset')


# ============================
# ASSET RELATIONSHIP
# ============================
class AssetRelationshipViewSet(viewsets.ModelViewSet):
    serializer_class = AssetRelationshipSerializer
    permission_classes = [IsAuthenticated, CanEditAssets]

    def get_queryset(self):
        return AssetRelationship.objects.filter(
            parent_asset__organization=self.request.user.organization
        ).select_related('parent_asset', 'child_asset')


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Asset

@login_required
def asset_list(request):
    return render(request, "assets/asset_list.html", {
        "assets": Asset.objects.all()
    })

@login_required
def asset_detail(request, pk):
    asset = Asset.objects.get(pk=pk)
    return render(request, "assets/asset_detail.html", {"asset": asset})
