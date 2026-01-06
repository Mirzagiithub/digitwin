from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Organization, CustomUser, UserSession, AuditLog


# ============================
# ORGANIZATION ADMIN
# ============================
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'domain',
        'subscription_tier',
        'is_active',
        'user_count_display',
        'asset_count_display',
        'created_at',
    )
    list_filter = ('subscription_tier', 'is_active', 'is_trial', 'created_at')
    search_fields = ('name', 'domain', 'contact_email')
    readonly_fields = (
        'created_at',
        'updated_at',
        'user_count_display',
        'asset_count_display',
    )

    fieldsets = (
        (_('Organization Info'), {'fields': ('name', 'domain', 'slug')}),
        (_('Subscription'), {
            'fields': (
                'subscription_tier',
                'subscription_start',
                'subscription_end',
                'asset_limit',
                'user_limit',
                'data_retention_days',
            )
        }),
        (_('Status'), {'fields': ('is_active', 'is_trial')}),
        (_('Contact Information'), {'fields': ('contact_email', 'contact_phone', 'address')}),
        (_('Settings'), {'fields': ('timezone', 'currency', 'language')}),
        (_('Statistics'), {'fields': ('user_count_display', 'asset_count_display')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
    )

    def user_count_display(self, obj):
        return obj.user_count
    user_count_display.short_description = 'Total Users'

    def asset_count_display(self, obj):
        return obj.asset_count
    asset_count_display.short_description = 'Total Assets'


# ============================
# CUSTOM USER ADMIN
# ============================
@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser

    list_display = (
        'email',
        'organization',
        'role',
        'full_name',
        'is_active',
        'is_staff',
        'last_login',
        'login_count',
    )
    list_filter = (
        'organization',
        'role',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
    )
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {
            'fields': (
                'first_name',
                'last_name',
                'phone',
                'department',
                'job_title',
                'profile_picture',
            )
        }),
        (_('Organization'), {'fields': ('organization', 'role')}),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        (_('Security Status'), {
            'fields': (
                'email_verified',
                'phone_verified',
                'two_factor_enabled',
            )
        }),
        (_('Preferences'), {
            'fields': (
                'notifications_enabled',
                'email_notifications',
                'push_notifications',
                'language',
            )
        }),
        (_('Important Dates'), {
            'fields': (
                'last_login',
                'date_joined',
                'last_activity',
                'login_count',
            )
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'organization',
                'role',
                'password1',
                'password2',
                'is_active',
                'is_staff',
                'is_superuser',
            ),
        }),
    )

    readonly_fields = (
        'last_login',
        'date_joined',
        'last_activity',
        'login_count',
    )

    def get_fieldsets(self, request, obj=None):
        """
        Ensure correct form is used for add vs change.
        """
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)


# ============================
# USER SESSION ADMIN
# ============================
@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'ip_address',
        'device_type',
        'login_at',
        'logout_at',
        'is_active',
    )
    list_filter = ('device_type', 'is_active', 'login_at')
    search_fields = ('user__email', 'ip_address', 'location')
    readonly_fields = ('login_at', 'logout_at')
    date_hierarchy = 'login_at'


# ============================
# AUDIT LOG ADMIN (READ-ONLY)
# ============================
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        'action',
        'model',
        'object_id',
        'user',
        'organization',
        'timestamp',
        'ip_address',
    )
    list_filter = ('action', 'model', 'timestamp', 'organization')
    search_fields = (
        'user__email',
        'action',
        'model',
        'object_id',
        'ip_address',
    )
    readonly_fields = (
        'timestamp',
        'ip_address',
        'user_agent',
        'before_state',
        'after_state',
    )
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
