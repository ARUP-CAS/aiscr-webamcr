from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Vymaže z cache uloženou konfiguraci odstávky systému."""

    help = "Vymaže cache konfigurace odstávky systému."

    def handle(self, *args, **options):
        """Zneplatní pouze cache klíč odstávky systému.

        :param args: Poziční argumenty příkazu (nepoužívají se).
        :param options: Pojmenované argumenty příkazu (nepoužívají se).
        """
        cache.delete("maintenance")
        self.stdout.write(self.style.SUCCESS("Cache odstávky systému byla vymazána."))
