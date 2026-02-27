from django.apps import AppConfig


class FedoraManagementConfig(AppConfig):
    """Třída `FedoraManagementConfig` v modulu `webclient.fedora_management.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "fedora_management"
