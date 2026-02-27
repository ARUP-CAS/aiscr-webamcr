import logging
from typing import Union

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro generování a ukládání XML metadat.

    Tento příkaz zpracovává záznamy z databáze a pro každý záznam vygeneruje XML metadata
    podle AMČR schématu. Vygenerovaná metadata jsou následně uložena do Fedora repozitáře
    prostřednictvím metody save_metadata.

    Parametry:
        - --model: Název třídy modelu (např. Projekt, ArcheologickyZaznam). Pokud není zadán, zpracují se všechny dostupné modely
        - --limit: Maximální počet záznamů ke zpracování
        - --start-with-pk: Primární klíč, od kterého začít zpracování

    Příklady použití::

        python manage.py generate_metadata
        python manage.py generate_metadata --model Projekt --limit 100
        python manage.py generate_metadata --model Adb --start-with-pk 1000 --limit 50
    """

    help = _("core.management.commands.generate_metadata.Command.help")

    def add_arguments(self, parser):
        """Provádí operaci add arguments.
        
        :param parser: Vstupní hodnota ``parser`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        parser.add_argument(
            "--model",
            type=str,
            help=_("core.management.commands.generate_metadata.Command.add_arguments.model_help"),
            default=None,
        )
        parser.add_argument(
            "--limit",
            type=int,
            help=_("core.management.commands.generate_metadata.Command.add_arguments.limit_help"),
            default=None,
        )
        parser.add_argument(
            "--start-with-pk",
            type=int,
            help=_("core.management.commands.generate_metadata.Command.add_arguments.start_with_pk_help"),
            default=None,
        )

    def handle(self, *args, **options):
        """Zpracuje hodnotu.
        
        :param args: Dodatečné poziční argumenty předané voláním.
        :param options: Dodatečné pojmenované argumenty předané voláním.
        :return: Vrací výsledek provedené operace."""
        model_class = options.get("model")
        limit = options.get("limit")
        start_with_pk = options.get("start_with_pk")

        logger.debug(
            "core.management.commands.generate_metadata.start", extra={"class_name": model_class, "limit": limit}
        )
        if not model_class:
            from xml_generator.generator import DocumentGenerator

            for current_class in DocumentGenerator._get_schema_dict():
                logger.debug(
                    "core.management.commands.generate_metadata.loop_start",
                    extra={"limit": limit, "class_name": str(current_class)},
                )
                if not start_with_pk:
                    queryset = current_class.objects.all().order_by("pk")
                else:
                    queryset = current_class.objects.filter(pk__gte=start_with_pk).order_by("pk")
                if limit is not None:
                    queryset = queryset[:limit]
                for obj in queryset:
                    from core.repository_connector import FedoraTransaction
                    from uzivatel.models import User

                    obj: Union[ModelWithMetadata, User]
                    fedora_transaction = FedoraTransaction()
                    obj.save_metadata(fedora_transaction, close_transaction=True)
                logger.debug(
                    "core.management.commands.generate_metadata.loop_end",
                    extra={"limit": limit, "class_name": str(current_class)},
                )
        else:
            logger.debug(
                "core.management.commands.generate_metadata.loop_start",
                extra={"class_name": model_class, "limit": limit},
            )
            from adb.models import Adb
            from arch_z.models import ArcheologickyZaznam
            from dokument.models import Dokument, Let
            from ez.models import ExterniZdroj
            from heslar.models import Heslar, RuianKatastr, RuianKraj, RuianOkres
            from pas.models import SamostatnyNalez
            from pian.models import Pian
            from projekt.models import Projekt
            from uzivatel.models import Organizace, Osoba, User

            model_class = {
                "Projekt": Projekt,
                "ArcheologickyZaznam": ArcheologickyZaznam,
                "Let": Let,
                "Adb": Adb,
                "Dokument": Dokument,
                "ExterniZdroj": ExterniZdroj,
                "Pian": Pian,
                "SamostatnyNalez": SamostatnyNalez,
                "User": User,
                "Heslar": Heslar,
                "RuianKraj": RuianKraj,
                "RuianOkres": RuianOkres,
                "RuianKatastr": RuianKatastr,
                "Organizace": Organizace,
                "Osoba": Osoba,
            }.get(model_class)
            if not start_with_pk:
                queryset = model_class.objects.order_by("pk").all()
            else:
                queryset = model_class.objects.filter(pk__gte=start_with_pk).order_by("pk")
            if limit is not None:
                queryset = queryset[:limit]
            for obj in queryset:
                from core.repository_connector import FedoraTransaction

                obj: Union[ModelWithMetadata, User]
                fedora_transaction = FedoraTransaction()
                obj.active_transaction = fedora_transaction
                obj.save_metadata(fedora_transaction, close_transaction=True)
            logger.debug(
                "core.management.commands.generate_metadata.loop_end", extra={"class_name": model_class, "limit": limit}
            )
        logger.debug(
            "core.management.commands.generate_metadata.end", extra={"class_name": model_class, "limit": limit}
        )
