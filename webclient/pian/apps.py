from django.apps import AppConfig


class PianConfig(AppConfig):
    """Třída `PianConfig` v modulu `webclient.pian.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    name = "pian"

    def ready(self):
        """Funkce `PianConfig.ready` v modulu `webclient.pian.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(PianConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import pian.signals
