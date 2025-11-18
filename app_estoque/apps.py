from django.apps import AppConfig

class AppEstoqueConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_estoque'

    def ready(self):
        from .scheduler import iniciar_scheduler
        iniciar_scheduler()
