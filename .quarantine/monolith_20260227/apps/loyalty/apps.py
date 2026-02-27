from django.apps import AppConfig


class LoyaltyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.loyalty'
    verbose_name = 'Loyalty Program'
    
    def ready(self):
        """Initialize app when Django starts"""
        # Import signal handlers if any
        pass