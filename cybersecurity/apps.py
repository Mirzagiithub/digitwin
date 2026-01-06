from django.apps import AppConfig


class CybersecurityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cybersecurity'
    verbose_name = 'Cybersecurity'

    def ready(self):
        # Safely import signals (prevents circular imports & double registration)
        try:
            from . import signals  # noqa
        except ImportError:
            pass
