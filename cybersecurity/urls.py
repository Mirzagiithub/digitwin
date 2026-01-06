from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SecurityDigitalTwinViewSet,
    ZeroTrustPolicyViewSet,
    ThreatDetectionRuleViewSet,
    ThreatDetectionEventViewSet,
    AttackCampaignViewSet,threat_events,
)

app_name = 'cybersecurity'

router = DefaultRouter()
router.register(r'security-twins', SecurityDigitalTwinViewSet, basename='security-twin')
router.register(r'zero-trust-policies', ZeroTrustPolicyViewSet, basename='zero-trust-policy')
router.register(r'threat-detection-rules', ThreatDetectionRuleViewSet, basename='threat-detection-rule')
router.register(r'threat-detection-events', ThreatDetectionEventViewSet, basename='threat-detection-event')
router.register(r'attack-campaigns', AttackCampaignViewSet, basename='attack-campaign')

urlpatterns = [
    path('', include(router.urls)),
     path("threats/", threat_events, name="threat-events"),
]
