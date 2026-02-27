from django.apps import AppConfig


class DokumentConfig(AppConfig):
    """Třída `DokumentConfig` v modulu `webclient.dokument.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    name = "dokument"

    def ready(self):
        """Funkce `DokumentConfig.ready` v modulu `webclient.dokument.apps`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        super(DokumentConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import dokument.signals
