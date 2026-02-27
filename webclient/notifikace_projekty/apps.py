from django.apps import AppConfig


class NotifikaceProjektyConfig(AppConfig):
    """Třída `NotifikaceProjektyConfig` v modulu `webclient.notifikace_projekty.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifikace_projekty"

    def ready(self):
        """Funkce `NotifikaceProjektyConfig.ready` v modulu `webclient.notifikace_projekty.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(NotifikaceProjektyConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import notifikace_projekty.signals
