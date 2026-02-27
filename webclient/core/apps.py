from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Implementuje komponentu ``CoreConfig`` v rámci aplikace."""
    name = "core"

    def ready(self):
        """Provádí operaci ready.
        
        :return: Vrací výsledek provedené operace."""
        super(CoreConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import core.signals
