from django.apps import AppConfig


class IotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'iot'
    verbose_name = 'IoT'

    def ready(self):
        # Safe signal import (prevents circular imports & double registration)
        try:
            from . import signals  # noqa
        except ImportError:
            pass
