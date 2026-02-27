from django.apps import AppConfig


class PasConfig(AppConfig):
    """Třída `PasConfig` v modulu `webclient.pas.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    name = "pas"

    def ready(self):
        """Funkce `PasConfig.ready` v modulu `webclient.pas.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(PasConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import pas.signals
