from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SimulationScenarioViewSet,
    SimulationResultViewSet,
    DigitalTwinViewSet,
    PredictiveModelViewSet,
    PredictionViewSet,scenarios
)

router = DefaultRouter()
router.register(r'scenarios', SimulationScenarioViewSet, basename='scenario')
router.register(r'results', SimulationResultViewSet, basename='result')
router.register(r'digital-twins', DigitalTwinViewSet, basename='digital-twin')
router.register(r'predictive-models', PredictiveModelViewSet, basename='predictive-model')
router.register(r'predictions', PredictionViewSet, basename='prediction')

urlpatterns = [
    path('', include(router.urls)),
    path("bad", scenarios, name="simulation-scenarios"),
]
