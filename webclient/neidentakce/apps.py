from django.apps import AppConfig


class NeidentakceConfig(AppConfig):
    """Implementuje komponentu ``NeidentakceConfig`` v rámci aplikace."""

    name = "neidentakce"

    def ready(self):
        """Provádí operaci ready.

        :return: Vrací výsledek provedené operace."""
        super(NeidentakceConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import neidentakce.signals
