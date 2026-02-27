from django.apps import AppConfig


class EzConfig(AppConfig):
    """Třída `EzConfig` v modulu `webclient.ez.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    name = "ez"

    def ready(self):
        """Funkce `EzConfig.ready` v modulu `webclient.ez.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(EzConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import ez.signals
