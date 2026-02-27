from django.apps import AppConfig


class UzivatelConfig(AppConfig):
    """Implementuje komponentu ``UzivatelConfig`` v rámci aplikace."""

    name = "uzivatel"

    def ready(self):
        """Provádí operaci ready.

        :return: Vrací výsledek provedené operace."""
        super(UzivatelConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import uzivatel.signals
