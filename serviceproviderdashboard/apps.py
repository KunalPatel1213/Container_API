from django.apps import AppConfig


class ServiceproviderdashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'serviceproviderdashboard'

    def ready(self):
        import serviceproviderdashboard.signals  # noqa: F401
