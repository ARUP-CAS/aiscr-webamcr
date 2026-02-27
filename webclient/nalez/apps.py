from django.apps import AppConfig


class NalezConfig(AppConfig):
    """Třída `NalezConfig` v modulu `webclient.nalez.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    name = "nalez"

    def ready(self):
        """Funkce `NalezConfig.ready` v modulu `webclient.nalez.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(NalezConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import nalez.signals
