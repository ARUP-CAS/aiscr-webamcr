from django.apps import AppConfig


class HistorieConfig(AppConfig):
    """Třída `HistorieConfig` v modulu `webclient.historie.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    name = "historie"

    def ready(self):
        """Funkce `HistorieConfig.ready` v modulu `webclient.historie.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(HistorieConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import historie.signals
