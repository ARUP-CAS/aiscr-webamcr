from django.apps import AppConfig


class UzivatelConfig(AppConfig):
    """Zapouzdřuje chování třídy ``UzivatelConfig`` pro modul ``webclient.uzivatel.apps``."""
    name = "uzivatel"

    def ready(self):
        """Provádí funkci ``UzivatelConfig.ready`` v rámci modulu ``webclient.uzivatel.apps``."""
        super(UzivatelConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import uzivatel.signals
