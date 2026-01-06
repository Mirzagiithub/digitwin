from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import login, logout
from django.utils import timezone

from .models import Organization, CustomUser, UserSession, AuditLog
from .serializers import (
    OrganizationSerializer,
    UserSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    ProfileUpdateSerializer
)
from .permissions import IsOrganizationAdmin, IsSuperAdmin

import logging

logger = logging.getLogger(__name__)


# ============================
# ORGANIZATION
# ============================
class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    lookup_field = 'slug'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Organization.objects.all()
        return Organization.objects.filter(pk=user.organization_id)

    @action(detail=True, methods=['get'])
    def stats(self, request, slug=None):
        organization = self.get_object()

        stats = {
            'total_users': organization.user_count,
            'total_assets': organization.asset_count,
            'active_users': organization.users.filter(is_active=True).count(),
            'active_sessions': UserSession.objects.filter(
                user__organization=organization,
                is_active=True
            ).count(),
            'recent_audit_logs': AuditLog.objects.filter(
                organization=organization
            ).count(),
            'subscription_status': {
                'tier': organization.subscription_tier,
                'is_active': organization.is_subscription_active,
                'days_remaining': (
                    (organization.subscription_end - timezone.now().date()).days
                    if organization.subscription_end else None
                )
            }
        }
        return Response(stats)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, slug=None):
        organization = self.get_object()
        organization.is_active = False
        organization.save(update_fields=['is_active'])
        return Response({'status': 'Organization deactivated'})

    @action(detail=True, methods=['post'])
    def activate(self, request, slug=None):
        organization = self.get_object()
        organization.is_active = True
        organization.save(update_fields=['is_active'])
        return Response({'status': 'Organization activated'})


# ============================
# USERS
# ============================
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOrganizationAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return CustomUser.objects.all()
        return CustomUser.objects.filter(organization=user.organization)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization'] = self.request.user.organization
        return context

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': 'Wrong password'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(serializer.validated_data['new_password'])
            user.save(update_fields=['password'])
            return Response({'status': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        if user == request.user:
            return Response(
                {'error': 'Cannot deactivate yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response({'status': 'User deactivated'})

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=['is_active'])
        return Response({'status': 'User activated'})


# ============================
# AUTH
# ============================
class AuthViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        login(request, user)

        return Response({
            'user': UserSerializer(user).data,
            'organization': {
                'id': str(user.organization.id),
                'name': user.organization.name,
                'slug': user.organization.slug
            } if user.organization else None
        })

    @action(detail=False, methods=['post'])
    def logout(self, request):
        logout(request)
        return Response({'status': 'Logged out successfully'})


# ============================
# ERROR HANDLERS
# ============================
def bad_request(request, exception):
    return Response({'error': 'Bad Request'}, status=400)

def permission_denied(request, exception):
    return Response({'error': 'Permission Denied'}, status=403)

def page_not_found(request, exception):
    return Response({'error': 'Page Not Found'}, status=404)

def server_error(request):
    return Response({'error': 'Server Error'}, status=500)
