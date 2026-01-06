from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from django.utils import timezone
from django.db.models import Count, Avg, Max, Min, Q, F

from .models import (
    SimulationScenario, SimulationResult,
    DigitalTwin, PredictiveModel, Prediction
)
from .serializers import (
    SimulationScenarioSerializer, SimulationResultSerializer,
    DigitalTwinSerializer, PredictiveModelSerializer, PredictionSerializer
)
from core.permissions import CanViewAnalytics, CanEditAssets


# =====================================================
# Simulation Scenarios
# =====================================================
class SimulationScenarioViewSet(viewsets.ModelViewSet):
    serializer_class = SimulationScenarioSerializer
    permission_classes = [IsAuthenticated, CanEditAssets]

    def get_queryset(self):
        return SimulationScenario.objects.filter(
            organization=self.request.user.organization
        ).select_related(
            'organization', 'created_by'
        ).prefetch_related('target_assets')

    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.user.organization,
            created_by=self.request.user
        )

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        scenario = self.get_object()

        if scenario.status in ['running', 'completed']:
            return Response(
                {'error': 'Simulation already running or completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from .tasks import run_simulation_task
        run_simulation_task.delay(str(scenario.id))

        return Response({
            'status': 'Simulation queued',
            'simulation_id': str(scenario.id)
        })

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        scenario = self.get_object()

        if scenario.status != 'running':
            return Response(
                {'error': 'Simulation is not running'},
                status=status.HTTP_400_BAD_REQUEST
            )

        scenario.status = 'cancelled'
        scenario.actual_end = timezone.now()
        scenario.save(update_fields=['status', 'actual_end'])

        return Response({'status': 'Simulation cancelled'})

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        scenario = self.get_object()
        serializer = SimulationResultSerializer(
            scenario.results.all(), many=True
        )
        return Response(serializer.data)


# =====================================================
# Simulation Results
# =====================================================
class SimulationResultViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SimulationResultSerializer
    permission_classes = [IsAuthenticated, CanViewAnalytics]

    def get_queryset(self):
        return SimulationResult.objects.filter(
            scenario__organization=self.request.user.organization
        ).select_related('scenario')


# =====================================================
# Digital Twins
# =====================================================
class DigitalTwinViewSet(viewsets.ModelViewSet):
    serializer_class = DigitalTwinSerializer
    permission_classes = [IsAuthenticated, CanEditAssets]

    def get_queryset(self):
        return DigitalTwin.objects.filter(
            asset__organization=self.request.user.organization
        ).select_related('asset', 'asset__asset_type')

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        twin = self.get_object()

        twin.sync_status = 'synced'
        twin.current_state = {
            'status': 'operational',
            'last_sync': timezone.now().isoformat(),
            'metrics': {}
        }
        twin.save(update_fields=['sync_status', 'current_state'])

        return Response({
            'status': 'Digital twin synchronized',
            'twin_id': str(twin.id)
        })

    @action(detail=True, methods=['post'])
    def simulate(self, request, pk=None):
        twin = self.get_object()
        parameters = request.data.get('parameters', {})

        return Response({
            'twin_id': str(twin.id),
            'simulation_type': 'what_if',
            'parameters': parameters,
            'results': {
                'predicted_state': {},
                'metrics': {},
                'warnings': []
            },
            'simulated_at': timezone.now().isoformat()
        })


# =====================================================
# Predictive Models
# =====================================================
class PredictiveModelViewSet(viewsets.ModelViewSet):
    serializer_class = PredictiveModelSerializer
    permission_classes = [IsAuthenticated, CanEditAssets]

    def get_queryset(self):
        return PredictiveModel.objects.filter(
            organization=self.request.user.organization
        ).select_related('organization')

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)

    @action(detail=True, methods=['post'])
    def train(self, request, pk=None):
        model = self.get_object()

        if model.status == 'training':
            return Response(
                {'error': 'Model is already training'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from .tasks import train_model_task
        train_model_task.delay(str(model.id))

        return Response({
            'status': 'Training queued',
            'model_id': str(model.id)
        })

    @action(detail=True, methods=['post'])
    def predict(self, request, pk=None):
        model = self.get_object()
        asset_id = request.data.get('asset_id')
        input_features = request.data.get('input_features', {})

        if not asset_id:
            return Response(
                {'error': 'asset_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        prediction = Prediction.objects.create(
            model=model,
            asset_id=asset_id,
            input_features=input_features,
            prediction_value=0.85,   # mock
            confidence=0.92,         # mock
            metadata={'source': 'api'}
        )

        return Response(
            PredictionSerializer(prediction).data,
            status=status.HTTP_201_CREATED
        )


# =====================================================
# Predictions
# =====================================================
class PredictionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PredictionSerializer
    permission_classes = [IsAuthenticated, CanViewAnalytics]

    def get_queryset(self):
        return Prediction.objects.filter(
            asset__organization=self.request.user.organization
        ).select_related('model', 'asset')

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        queryset = self.get_queryset()

        model_id = request.query_params.get('model_id')
        asset_id = request.query_params.get('asset_id')

        if model_id:
            queryset = queryset.filter(model_id=model_id)
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)

        stats = queryset.aggregate(
            total_predictions=Count('id'),
            avg_confidence=Avg('confidence'),
            min_confidence=Min('confidence'),
            max_confidence=Max('confidence')
        )

        # Accuracy (±10% tolerance)
        with_actual = queryset.filter(actual_value__isnull=False)
        accurate = with_actual.filter(
            prediction_value__gte=F('actual_value') - 0.1,
            prediction_value__lte=F('actual_value') + 0.1
        ).count()

        stats['accuracy'] = (
            accurate / with_actual.count()
            if with_actual.exists() else None
        )

        return Response(stats)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import SimulationScenario

@login_required
def scenarios(request):
    return render(request, "simulation/scenarios.html", {
        "scenarios": SimulationScenario.objects.all()
    })
