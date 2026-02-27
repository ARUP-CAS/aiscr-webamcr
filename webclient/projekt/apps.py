from django.apps import AppConfig


class ProjektConfig(AppConfig):
    """Třída `ProjektConfig` v modulu `webclient.projekt.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    name = "projekt"

    def ready(self):
        """Funkce `ProjektConfig.ready` v modulu `webclient.projekt.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(ProjektConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import projekt.signals
