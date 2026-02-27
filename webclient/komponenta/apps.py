from django.apps import AppConfig


class KomponentaConfig(AppConfig):
    """Implementuje komponentu ``KomponentaConfig`` v rámci aplikace."""
    name = "komponenta"

    def ready(self):
        """Provádí operaci ready.
        
        :return: Vrací výsledek provedené operace."""
        super(KomponentaConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import komponenta.signals
