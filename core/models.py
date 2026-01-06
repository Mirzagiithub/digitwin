from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid


# ============================
# ORGANIZATION
# ============================
class OrganizationManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)


class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    domain = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    subscription_tier = models.CharField(
        max_length=20,
        choices=[
            ('starter', 'Starter'),
            ('professional', 'Professional'),
            ('enterprise', 'Enterprise'),
        ],
        default='starter',
    )

    subscription_start = models.DateField(default=timezone.now)
    subscription_end = models.DateField(null=True, blank=True)

    asset_limit = models.IntegerField(default=100)
    user_limit = models.IntegerField(default=1)
    data_retention_days = models.IntegerField(default=90)

    is_active = models.BooleanField(default=True)
    is_trial = models.BooleanField(default=True)

    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    timezone = models.CharField(max_length=50, default='UTC')
    currency = models.CharField(max_length=3, default='USD')
    language = models.CharField(max_length=10, default='en')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OrganizationManager()

    class Meta:
        db_table = 'organizations'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.subscription_tier})"

    @property
    def is_subscription_active(self):
        if self.subscription_end:
            return self.subscription_end >= timezone.now().date()
        return True

    @property
    def user_count(self):
        return self.users.count()

    @property
    def asset_count(self):
        # Assets app not linked yet
        return 0


# ============================
# CUSTOM USER
# ============================
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_active', True)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True,
    )

    role = models.CharField(
        max_length=30,
        choices=[
            ('superadmin', 'Super Administrator'),
            ('org_admin', 'Organization Admin'),
            ('manager', 'Manager'),
            ('operator', 'Operator'),
            ('viewer', 'Viewer'),
            ('analyst', 'Analyst'),
            ('maintenance', 'Maintenance Technician'),
        ],
        default='viewer',
    )

    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
    )

    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)

    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    login_count = models.IntegerField(default=0)

    notifications_enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=False)
    language = models.CharField(max_length=10, default='en')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_org_admin(self):
        return self.role in ['superadmin', 'org_admin']

    @property
    def can_edit_assets(self):
        return self.role in ['superadmin', 'org_admin', 'manager', 'operator']

    @property
    def can_view_analytics(self):
        return self.role in ['superadmin', 'org_admin', 'manager', 'analyst']

    def update_last_activity(self):
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])


# ============================
# USER SESSION
# ============================
class UserSession(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True)

    login_at = models.DateTimeField(auto_now_add=True)
    logout_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_sessions'
        ordering = ['-login_at']

    def __str__(self):
        return f"{self.user.email} - {self.login_at}"


# ============================
# AUDIT LOG
# ============================
class AuditLog(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='audit_logs',
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    action = models.CharField(max_length=100)
    model = models.CharField(max_length=50)
    object_id = models.CharField(max_length=100)

    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)

    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['organization', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['model', 'object_id']),
        ]

    def __str__(self):
        return f"{self.action} on {self.model}"
