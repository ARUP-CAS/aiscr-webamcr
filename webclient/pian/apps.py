from django.apps import AppConfig


class PianConfig(AppConfig):
    """Implementuje komponentu ``PianConfig`` v rámci aplikace."""
    name = "pian"

    def ready(self):
        """Provádí operaci ready.
        
        :return: Vrací výsledek provedené operace."""
        super(PianConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import pian.signals
