from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta

from .models import (
    SecurityDigitalTwin,
    ZeroTrustPolicy,
    ThreatDetectionRule,
    ThreatDetectionEvent,
    AttackCampaign,
)
from .serializers import (
    SecurityDigitalTwinSerializer,
    ZeroTrustPolicySerializer,
    ThreatDetectionRuleSerializer,
    ThreatDetectionEventSerializer,
    AttackCampaignSerializer,
)
from core.permissions import CanViewAnalytics, IsOrganizationAdmin


# ============================
# SECURITY DIGITAL TWIN
# ============================
class SecurityDigitalTwinViewSet(viewsets.ModelViewSet):
    serializer_class = SecurityDigitalTwinSerializer
    permission_classes = [IsAuthenticated, CanViewAnalytics]

    def get_queryset(self):
        return SecurityDigitalTwin.objects.filter(
            organization=self.request.user.organization
        ).select_related('asset', 'asset__asset_type')

    @action(detail=True, methods=['post'])
    def recalculate_score(self, request, pk=None):
        twin = self.get_object()

        zero_trust_weight = 0.3
        threat_weight = 0.4
        compliance_weight = 0.3

        threat_factor = 0.3 if twin.active_threats else 0.9
        zero_trust_factor = 0.9 if twin.zero_trust_status == 'enforced' else 0.5
        compliance_factor = 0.8

        score = (
            zero_trust_factor * zero_trust_weight +
            threat_factor * threat_weight +
            compliance_factor * compliance_weight
        ) * 100

        twin.security_score = round(score, 2)

        if score >= 80:
            twin.risk_level = 'low'
        elif score >= 60:
            twin.risk_level = 'medium'
        elif score >= 40:
            twin.risk_level = 'high'
        else:
            twin.risk_level = 'critical'

        twin.save(update_fields=['security_score', 'risk_level'])

        return Response({
            'security_score': twin.security_score,
            'risk_level': twin.risk_level,
        })


# ============================
# ZERO TRUST POLICY
# ============================
class ZeroTrustPolicyViewSet(viewsets.ModelViewSet):
    serializer_class = ZeroTrustPolicySerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    def get_queryset(self):
        return ZeroTrustPolicy.objects.filter(
            organization=self.request.user.organization
        ).select_related('organization', 'created_by').prefetch_related('assets')

    @action(detail=True, methods=['get'])
    def compliance(self, request, pk=None):
        policy = self.get_object()

        score = 0
        if policy.enforcement_status == 'fully_enforced':
            score = 90
        elif policy.enforcement_status == 'partial':
            score = 60
        else:
            score = 30

        return Response({
            'policy': policy.name,
            'enforcement_status': policy.enforcement_status,
            'compliance_score': score,
        })


# ============================
# THREAT DETECTION RULE
# ============================
class ThreatDetectionRuleViewSet(viewsets.ModelViewSet):
    serializer_class = ThreatDetectionRuleSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    def get_queryset(self):
        return ThreatDetectionRule.objects.filter(
            organization=self.request.user.organization
        ).select_related('created_by')

    @action(detail=True, methods=['get'])
    def effectiveness(self, request, pk=None):
        rule = self.get_object()

        total = rule.detection_count
        false_pos = rule.false_positive_count

        precision = (total - false_pos) / total if total else 0

        return Response({
            'rule': rule.name,
            'detections': total,
            'false_positives': false_pos,
            'precision': round(precision, 2),
        })


# ============================
# THREAT DETECTION EVENT
# ============================
class ThreatDetectionEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ThreatDetectionEventSerializer
    permission_classes = [IsAuthenticated, CanViewAnalytics]

    def get_queryset(self):
        return ThreatDetectionEvent.objects.filter(
            organization=self.request.user.organization
        ).select_related('rule', 'asset')

    @action(detail=False, methods=['get'])
    def summary(self, request):
        time_range = request.query_params.get('time_range', '24h')
        since = self._get_time_filter(time_range)

        events = self.get_queryset().filter(timestamp__gte=since)

        return Response({
            'total': events.count(),
            'by_severity': list(
                events.values('severity').annotate(count=Count('id'))
            ),
            'investigated': events.filter(investigated=True).count(),
            'time_range': time_range,
        })

    def _get_time_filter(self, time_range):
        now = timezone.now()
        mapping = {
            '1h': timedelta(hours=1),
            '6h': timedelta(hours=6),
            '24h': timedelta(days=1),
            '7d': timedelta(days=7),
            '30d': timedelta(days=30),
        }
        return now - mapping.get(time_range, timedelta(days=1))


# ============================
# ATTACK CAMPAIGN
# ============================
class AttackCampaignViewSet(viewsets.ModelViewSet):
    serializer_class = AttackCampaignSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    def get_queryset(self):
        return AttackCampaign.objects.filter(
            organization=self.request.user.organization
        ).select_related('organization', 'created_by').prefetch_related('target_assets')

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        campaign = self.get_object()

        if campaign.status != 'planned':
            return Response(
                {'error': 'Campaign must be planned to start'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        campaign.status = 'running'
        campaign.save(update_fields=['status'])

        return Response({'status': 'Campaign started'})

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        campaign = self.get_object()

        if campaign.status != 'running':
            return Response(
                {'error': 'Campaign is not running'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        campaign.status = 'completed'
        campaign.save(update_fields=['status'])

        return Response({'status': 'Campaign completed'})


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ThreatDetectionEvent

@login_required
def threat_events(request):
    events = ThreatDetectionEvent.objects.order_by("-timestamp")
    return render(request, "cybersecurity/threat_events.html", {
        "events": events
    })
