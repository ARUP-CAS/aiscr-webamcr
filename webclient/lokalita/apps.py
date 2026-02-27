from django.apps import AppConfig


class LokalitaConfig(AppConfig):
    """Třída `LokalitaConfig` v modulu `webclient.lokalita.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "lokalita"

    def ready(self):
        """Funkce `LokalitaConfig.ready` v modulu `webclient.lokalita.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(LokalitaConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import lokalita.signals
