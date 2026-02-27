from django.apps import AppConfig


class KomponentaConfig(AppConfig):
    """Třída `KomponentaConfig` v modulu `webclient.komponenta.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    name = "komponenta"

    def ready(self):
        """Funkce `KomponentaConfig.ready` v modulu `webclient.komponenta.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(KomponentaConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import komponenta.signals
