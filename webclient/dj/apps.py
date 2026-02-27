from django.apps import AppConfig


class DjConfig(AppConfig):
    """Třída `DjConfig` v modulu `webclient.dj.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    name = "dj"

    def ready(self):
        """Funkce `DjConfig.ready` v modulu `webclient.dj.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(DjConfig, self).ready()
        import dj.signals
