from django.apps import AppConfig


class ArchZConfig(AppConfig):
    """Třída `ArchZConfig` v modulu `webclient.arch_z.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    name = "arch_z"

    def ready(self):
        """Funkce `ArchZConfig.ready` v modulu `webclient.arch_z.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(ArchZConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import arch_z.signals
