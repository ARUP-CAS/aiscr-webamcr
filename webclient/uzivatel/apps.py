from django.apps import AppConfig


class UzivatelConfig(AppConfig):
    """Třída `UzivatelConfig` v modulu `webclient.uzivatel.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    name = "uzivatel"

    def ready(self):
        """Funkce `UzivatelConfig.ready` v modulu `webclient.uzivatel.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(UzivatelConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import uzivatel.signals
