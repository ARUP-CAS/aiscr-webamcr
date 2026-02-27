from django.apps import AppConfig


class AdbConfig(AppConfig):
    """Třída `AdbConfig` v modulu `webclient.adb.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    name = "adb"

    def ready(self):
        """Funkce `AdbConfig.ready` v modulu `webclient.adb.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(AdbConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import adb.signals
