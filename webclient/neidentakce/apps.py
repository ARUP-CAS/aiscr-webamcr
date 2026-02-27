from django.apps import AppConfig


class NeidentakceConfig(AppConfig):
    """Třída `NeidentakceConfig` v modulu `webclient.neidentakce.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    name = "neidentakce"

    def ready(self):
        """Funkce `NeidentakceConfig.ready` v modulu `webclient.neidentakce.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(NeidentakceConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import neidentakce.signals
