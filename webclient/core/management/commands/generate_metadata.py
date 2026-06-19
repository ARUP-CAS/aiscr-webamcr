import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import requests
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)

_RETRYABLE_EXCEPTIONS = (requests.exceptions.ConnectionError, requests.exceptions.Timeout)


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
        """
        Registruje příkazové argumenty pro filtrování a limitování zpracování záznamů.

        :param parser: Argumentový parser pro přidání nových parametrů příkazu.
        """
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
        parser.add_argument(
            "--workers",
            type=int,
            help=_("core.management.commands.generate_metadata.Command.add_arguments.workers_help"),
            default=1,
        )
        parser.add_argument(
            "--max-retries",
            type=int,
            help=_("core.management.commands.generate_metadata.Command.add_arguments.max_retries_help"),
            default=3,
        )

    @staticmethod
    def _process_object(obj, max_retries=3):
        """
        Zpracuje jeden záznam — vytvoří novou Fedora transakci a uloží metadata.

        Funkce je bezpečná pro volání z více vláken: každý záznam dostane vlastní
        ``FedoraTransaction``. Přechodné síťové chyby (např. vyčerpání efemerálních
        portů, timeout) jsou opakovány s exponenciálním backoffem.

        :param obj: Instance modelu, pro kterou mají být uložena XML metadata.
        :param max_retries: Maximální počet opakování při přechodných síťových chybách.
        """
        from core.repository_connector import FedoraNoResponseError, FedoraTransaction

        attempt = 0
        while True:
            fedora_transaction = None
            try:
                fedora_transaction = FedoraTransaction()
                obj.active_transaction = fedora_transaction
                obj.save_metadata(fedora_transaction, close_transaction=True)
                return
            except (FedoraNoResponseError, *_RETRYABLE_EXCEPTIONS) as exc:
                if fedora_transaction is not None:
                    try:
                        fedora_transaction.rollback_transaction()
                    except Exception:
                        logger.warning(
                            "core.management.commands.generate_metadata.rollback_failed",
                            extra={"pk": getattr(obj, "pk", None)},
                            exc_info=True,
                        )
                attempt += 1
                if attempt > max_retries:
                    logger.error(
                        "core.management.commands.generate_metadata.retries_exhausted",
                        extra={"pk": getattr(obj, "pk", None), "attempts": attempt, "error": str(exc)},
                    )
                    raise
                backoff = min(30.0, 0.5 * (2 ** (attempt - 1))) + random.uniform(0, 0.5)
                logger.warning(
                    "core.management.commands.generate_metadata.retry",
                    extra={
                        "pk": getattr(obj, "pk", None),
                        "attempt": attempt,
                        "backoff": backoff,
                        "error": str(exc),
                    },
                )
                time.sleep(backoff)

    def _process_queryset(self, queryset, workers, max_retries=3, total=None, show_progress=False):
        """
        Projde queryset a pro každý záznam vyvolá ``_process_object``.

        Při ``workers > 1`` zpracovává záznamy paralelně přes ``ThreadPoolExecutor``;
        práce je I/O-bound (HTTP volání do Fedora repozitáře), takže vlákna pomáhají.
        Postup je synchronizován zámkem, aby se výpis nepřekrýval. Queryset je čten
        po chunkách přes ``.iterator()``, aby se nehromadily v paměti všechny záznamy
        při dlouhých dávkách.

        :param queryset: Django QuerySet záznamů ke zpracování.
        :param workers: Počet paralelních vláken (1 = sekvenční zpracování).
        :param max_retries: Maximální počet opakování při přechodných síťových chybách.
        :param total: Celkový počet záznamů pro výpočet progressu (pokud je znám).
        :param show_progress: Zda zapisovat průběh na stdout.
        """
        progress_lock = Lock()
        counter = {"done": 0}
        records = queryset.iterator(chunk_size=500) if hasattr(queryset, "iterator") else queryset

        def report(index):
            if not show_progress:
                return
            if total:
                percent = (index / total) * 100
                self.stdout.write(f"\r{index}/{total} ({percent:.1f}%)", ending="")
            else:
                self.stdout.write(f"\r{index}", ending="")
            self.stdout.flush()

        def worker(obj):
            try:
                self._process_object(obj, max_retries=max_retries)
            finally:
                close_old_connections()
            with progress_lock:
                counter["done"] += 1
                report(counter["done"])

        try:
            if workers and workers > 1:
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    list(executor.map(worker, records))
            else:
                for index, obj in enumerate(records, start=1):
                    self._process_object(obj, max_retries=max_retries)
                    report(index)
        finally:
            close_old_connections()

        if show_progress:
            self.stdout.write("")

    def handle(self, *args, **options):
        """
        Vygeneruje a uloží XML metadata pro AMČR záznamy do Fedora repozitáře.

        :param args: Poziční argumenty příkazu (nepoužívá se).
        :param options: Pojmenované argumenty (model, limit, start_with_pk) ze příkazového řádku.
        """
        model_class = options.get("model")
        limit = options.get("limit")
        start_with_pk = options.get("start_with_pk")
        workers = options.get("workers") or 1
        max_retries = options.get("max_retries")
        if max_retries is None:
            max_retries = 3

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
                self._process_queryset(queryset, workers, max_retries=max_retries)
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
            total = queryset.count()
            self._process_queryset(queryset, workers, max_retries=max_retries, total=total, show_progress=True)
            logger.debug(
                "core.management.commands.generate_metadata.loop_end", extra={"class_name": model_class, "limit": limit}
            )
        logger.debug(
            "core.management.commands.generate_metadata.end", extra={"class_name": model_class, "limit": limit}
        )
