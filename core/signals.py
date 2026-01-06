from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import user_logged_in, user_logged_out
from django.utils import timezone

from .models import AuditLog, CustomUser, UserSession
from .threadlocals import get_request


# ============================
# HELPERS
# ============================
def get_client_ip(request):
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def serialize_instance(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.name)
        data[field.name] = str(value.pk) if hasattr(value, 'pk') else value
    return data


def get_device_type(user_agent):
    ua = (user_agent or '').lower()
    if 'mobile' in ua:
        return 'mobile'
    if 'tablet' in ua:
        return 'tablet'
    if 'bot' in ua or 'crawler' in ua:
        return 'bot'
    return 'desktop'


# ============================
# AUDIT LOGGER
# ============================
class AuditLogger:
    @staticmethod
    def log_action(request, instance, action):
        if not request or not request.user.is_authenticated:
            return

        # Avoid recursive logging
        if instance.__class__.__name__ in {'AuditLog', 'UserSession'}:
            return

        try:
            AuditLog.objects.create(
                organization=getattr(request.user, 'organization', None),
                user=request.user,
                action=action,
                model=instance.__class__.__name__,
                object_id=str(instance.pk),
                after_state=serialize_instance(instance),
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
        except Exception:
            # Never crash the request
            pass


# ============================
# MODEL AUDIT SIGNALS
# ============================
@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    request = get_request()
    if not request:
        return

    action = 'CREATE' if created else 'UPDATE'
    AuditLogger.log_action(request, instance, action)


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    request = get_request()
    if not request:
        return

    AuditLogger.log_action(request, instance, 'DELETE')


# ============================
# AUTH SESSION SIGNALS
# ============================
@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    UserSession.objects.create(
        user=user,
        session_key=request.session.session_key,
        ip_address=ip_address,
        user_agent=user_agent,
        device_type=get_device_type(user_agent),
    )

    user.last_login_ip = ip_address
    user.login_count += 1
    user.save(update_fields=['last_login_ip', 'login_count'])

    if user.organization:
        AuditLog.objects.create(
            organization=user.organization,
            user=user,
            action='USER_LOGIN',
            model='CustomUser',
            object_id=str(user.pk),
            ip_address=ip_address,
            user_agent=user_agent,
        )


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    if not user:
        return

    session = user.sessions.filter(
        session_key=request.session.session_key,
        is_active=True,
    ).first()

    if session:
        session.logout_at = timezone.now()
        session.is_active = False
        session.save(update_fields=['logout_at', 'is_active'])
