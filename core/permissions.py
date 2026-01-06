from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class IsOrganizationAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, 'role', None) in ['superadmin', 'org_admin']
        )

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        user_org = getattr(user, 'organization', None)

        if hasattr(obj, 'organization'):
            return obj.organization == user_org

        if hasattr(obj, 'user') and obj.user:
            return obj.user.organization == user_org

        return False


class CanEditAssets(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(getattr(user, 'can_edit_assets', False))

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        obj_org = getattr(obj, 'organization', None)
        user_org = getattr(user, 'organization', None)

        return bool(
            getattr(user, 'can_edit_assets', False)
            and obj_org == user_org
        )


class CanViewAnalytics(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, 'can_view_analytics', False)
        )

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        obj_org = getattr(obj, 'organization', None)
        user_org = getattr(user, 'organization', None)

        return bool(
            getattr(user, 'can_view_analytics', False)
            and obj_org == user_org
        )


class IsObjectOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if hasattr(obj, 'user'):
            return obj.user == user

        if hasattr(obj, 'created_by'):
            return obj.created_by == user

        return False
