from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    verbose_name = 'Orders & Settlement'
    
    def ready(self):
        """Initialize app when Django starts"""
        # Import signal handlers if any
        pass