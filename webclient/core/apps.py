from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Třída `CoreConfig` v modulu `webclient.core.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    name = "core"

    def ready(self):
        """Funkce `CoreConfig.ready` v modulu `webclient.core.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(CoreConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import core.signals
