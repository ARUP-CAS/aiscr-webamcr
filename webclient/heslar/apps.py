from django.apps import AppConfig


class HeslarConfig(AppConfig):
    """Třída `HeslarConfig` v modulu `webclient.heslar.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    name = "heslar"

    def ready(self):
        """Funkce `HeslarConfig.ready` v modulu `webclient.heslar.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(HeslarConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import heslar.signals
