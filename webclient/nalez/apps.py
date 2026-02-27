from django.apps import AppConfig


class NalezConfig(AppConfig):
    """Implementuje komponentu ``NalezConfig`` v rámci aplikace."""
    name = "nalez"

    def ready(self):
        """Provádí operaci ready.
        
        :return: Vrací výsledek provedené operace."""
        super(NalezConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import nalez.signals
