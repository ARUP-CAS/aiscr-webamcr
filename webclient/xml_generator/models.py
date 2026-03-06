import logging
from typing import Optional

from celery import Celery
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.urls import reverse

logger = logging.getLogger(__name__)
UPDATE_REDIS_SNAPSHOT = 20


def check_if_task_queued(class_name, pk, task_name):
    """
    Ověří if task queued.

    :param class_name: Název nebo typ ``class_name`` používaný pro volbu cílové logiky.
    :param pk: Primární klíč zpracovávaného záznamu.
    :param task_name: Textový název nebo klíč ``task_name`` používaný v rámci operace.
    """
    try:
        app = Celery("webclient")
        app.config_from_object("django.conf:settings", namespace="CELERY")
        app.autodiscover_tasks()
        i = app.control.inspect(["worker1@amcr"])
        queues = (i.scheduled(),)
    except Exception as e:
        logger.warning(
            "xml_generator.models.ModelWithMetadata.check_if_task_queued.Celery_warning",
            extra={"exception": e, "app": app},
        )
        return False
    for queue in queues:
        if queue is None:
            logger.warning(
                "xml_generator.models.ModelWithMetadata.check_if_task_queued.warning",
                extra={"class_name": class_name, "pk": pk, "key": i, "queue": queues},
            )
            return False
        for queue_name, queue_tasks in queue.items():
            for task in queue_tasks:
                if (
                    "request" in task
                    and task_name in task.get("request").get("name").lower()
                    and tuple(task.get("request").get("args")[:2]) == (class_name, pk)
                ):
                    logger.debug(
                        "xml_generator.models.ModelWithMetadata.check_if_task_queued.already_scheduled",
                        extra={"class_name": class_name, "pk": pk},
                    )
                    return True
    return False


class BaseAmcrModel(models.Model):
    """Základní model pro všechny modely v aplikaci."""

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        abstract = True

    def __str__(self):
        """
               Vrací textovou reprezentaci objektu.

        Textová reprezentace objektu.
        """
        return f"{self.pk}"

    @property
    def get_ident_cely_link(self):
        """Vrací ident cely link."""
        if hasattr(self, "get_absolute_url") and hasattr(self, "ident_cely"):
            return f"<a href='{self.get_absolute_url()}' target='_blank'>{self.ident_cely}</a>"


class ModelWithMetadata(BaseAmcrModel):
    """Implementuje komponentu ``ModelWithMetadata`` v rámci aplikace."""

    IDENT_PREFIX = None
    SEQUENCE_NAME = None

    ident_cely = models.TextField(unique=True)

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        self.suppress_signal = False
        self.deleted_by_user = None
        self.active_transaction = None
        self.close_active_transaction_when_finished = False
        self.deletion_record_saved = False
        self.skip_container_check = False
        super(ModelWithMetadata, self).__init__(*args, **kwargs)

    def create_transaction(self, transaction_user, success_message=None, error_message=None):
        """
        Vytvoří transaction. v aplikaci.

        :param transaction_user: Uživatel nebo osoba ``transaction_user``, v jejímž kontextu se operace provádí.
        :param success_message: Textová zpráva ``success_message`` používaná pro hlášení stavu nebo chyby.
        :param error_message: Textová zpráva ``error_message`` používaná pro hlášení stavu nebo chyby.
        """
        from core.repository_connector import FedoraTransaction
        from uzivatel.models import User

        transaction_user: User
        self.active_transaction = FedoraTransaction(self, transaction_user, success_message, error_message)
        return self.active_transaction

    @property
    def metadata(self):
        """Provádí operaci metadata."""
        from core.repository_connector import FedoraRepositoryConnector

        connector = FedoraRepositoryConnector(self)
        return connector.get_metadata()

    def get_metadata_historicka(self, timestamp):
        """
        Metoda k získání vlastního souboru metadat dané verze z Fedory

        :param timestamp: Časový údaj použitý při filtrování nebo výpočtu.
        """
        from core.repository_connector import FedoraRepositoryConnector

        connector = FedoraRepositoryConnector(self)
        return connector.get_metadata_historicka(timestamp)

    def get_historicke_verze(self):
        """Metoda k získání údajů o historických verzích metadat ve Fedoře pro tabulku historie"""
        from core.repository_connector import FedoraRepositoryConnector
        from core.utils import get_timezone

        connector = FedoraRepositoryConnector(self)
        history_list = connector.get_historie_metadat()
        results = []
        timezone = get_timezone()
        for history_item in history_list:
            local_dt = history_item["datetime"].astimezone(timezone)
            url = reverse(
                "core:stahnout_data_historicka",
                kwargs={
                    "model_name": self.__class__.__name__,
                    "ident_cely": self.ident_cely,
                    "timestamp": history_item["timestamp"],
                },
            )
            results.append(
                {
                    "datum": local_dt,
                    "url": url,
                    "uzivatel": history_item["creator"],
                }
            )
        return results

    def save_metadata(
        self, fedora_transaction=None, include_files=False, close_transaction=False, skip_container_check=False
    ):
        """
        Uloží metadata. v aplikaci.

        :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.
        :param include_files: Příznak ``include_files`` určující průběh nebo rozsah zpracování.
        :param close_transaction: Příznak ``close_transaction`` určující průběh nebo rozsah zpracování.
        :param skip_container_check: Příznak ``skip_container_check`` určující průběh nebo rozsah zpracování.
        """
        from core.repository_connector import DryRunFedoraTransaction, FedoraDeletionOnlyTransaction, FedoraTransaction

        fedora_transaction = self._get_fedora_transaction(fedora_transaction)
        if isinstance(fedora_transaction, DryRunFedoraTransaction) or isinstance(
            fedora_transaction, FedoraDeletionOnlyTransaction
        ):
            fedora_transaction.add_updated_ident_cely(self.ident_cely)
            return
        if not self.ident_cely:
            logger.warning(
                "xml_generator.models.ModelWithMetadata.save_metadata.no_ident",
                extra={
                    "ident_cely": self.ident_cely,
                    "pk": self.pk,
                    "class_name": self.__class__.__name__,
                    "transaction": fedora_transaction.uid,
                    "close_transaction": close_transaction,
                },
            )
            return
        logger.debug(
            "xml_generator.models.ModelWithMetadata.save_metadata.start",
            extra={
                "ident_cely": self.ident_cely,
                "pk": self.pk,
                "class_name": self.__class__.__name__,
                "transaction": getattr(fedora_transaction, "uid", ""),
                "close_transaction": close_transaction,
            },
        )
        fedora_transaction: Optional[FedoraTransaction]
        from core.repository_connector import FedoraRepositoryConnector

        connector = FedoraRepositoryConnector(self, fedora_transaction, skip_container_check=self.skip_container_check)
        if include_files:
            from core.models import SouborVazby

            if hasattr(self, "soubory") and isinstance(self.soubory, SouborVazby):
                for soubor in self.soubory.soubory.all():
                    from core.models import Soubor

                    soubor: Soubor
                    connector.migrate_binary_file(soubor, include_content=False)
        connector.save_metadata(True)
        if close_transaction is True:
            logger.debug(
                "xml_generator.models.ModelWithMetadata.save_metadata.mark_transaction_as_closed",
                extra={"transaction": getattr(fedora_transaction, "uid", "")},
            )
            transaction.on_commit(lambda: fedora_transaction.mark_transaction_as_closed())
        logger.debug(
            "xml_generator.models.ModelWithMetadata.save_metadata.end",
            extra={
                "transaction": getattr(fedora_transaction, "uid", ""),
                "close_transaction": self.close_active_transaction_when_finished,
            },
        )

    def save_record_deletion_record(self, fedora_transaction, deleted_by_user=None):
        """
        Uloží record deletion record.

        :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.
        :param deleted_by_user: Příznak ``deleted_by_user`` určující průběh nebo rozsah zpracování.
        """
        fedora_transaction = self._get_fedora_transaction(fedora_transaction)

        from arch_z.models import ArcheologickyZaznam
        from dokument.models import Dokument
        from ez.models import ExterniZdroj
        from pas.models import SamostatnyNalez
        from pian.models import Pian
        from projekt.models import Projekt

        if deleted_by_user:
            self.deleted_by_user = deleted_by_user

        if (
            isinstance(self, ArcheologickyZaznam)
            or isinstance(self, Dokument)
            or isinstance(self, ExterniZdroj)
            or isinstance(self, Pian)
            or isinstance(self, Projekt)
            or isinstance(self, SamostatnyNalez)
        ) and self.deletion_record_saved is not True:
            from historie.models import Historie

            Historie.save_record_deletion_record(record=self)
            self.save_metadata(fedora_transaction, skip_container_check=True)
            self.deletion_record_saved = True

    def _get_fedora_transaction(self, fedora_transaction):
        """
        Vrací fedora transaction.

        :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.
        :return: Načtená data odpovídající zadaným vstupům.
        """
        if fedora_transaction is None and self.active_transaction is not None:
            fedora_transaction = self.active_transaction
        elif fedora_transaction is None and self.active_transaction is None:
            raise ValueError("No Fedora transaction")
        from core.repository_connector import BaseFedoraTransaction

        if not isinstance(fedora_transaction, BaseFedoraTransaction):
            raise ValueError("fedora_transaction must be a FedoraTransaction class object")
        return fedora_transaction

    def record_deletion(self, fedora_transaction=None, close_transaction=False):
        """
        Provádí operaci record deletion.

        :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.
        :param close_transaction: Příznak ``close_transaction`` určující průběh nebo rozsah zpracování.
        """
        logger.debug("xml_generator.models.ModelWithMetadata.record_deletion.start")

        fedora_transaction = self._get_fedora_transaction(fedora_transaction)
        from core.repository_connector import FedoraRepositoryConnector

        connector = FedoraRepositoryConnector(self, fedora_transaction, skip_container_check=True)
        if not self.deletion_record_saved:
            self.save_record_deletion_record(fedora_transaction)
        try:
            from core.models import SouborVazby

            if (
                hasattr(self, "soubory")
                and self.soubory is not None
                and isinstance(self.soubory, SouborVazby)
                and self.soubory.pk is not None
            ):
                for soubor in self.soubory.soubory.all():
                    from core.models import Soubor

                    soubor: Soubor
                    connector.delete_binary_file(soubor)
            logger.debug("xml_generator.models.ModelWithMetadata.record_deletion.end")
            from dokument.models import Dokument
            from pas.models import SamostatnyNalez

            if isinstance(self, Dokument):
                if hasattr(self, "soubory") and self.soubory.pk is not None:
                    for item in self.soubory.soubory.all():
                        item.suppress_signal = True
                        item.delete()
                    self.soubory.delete()
            elif isinstance(self, SamostatnyNalez):
                if hasattr(self, "soubory") and self.soubory.pk is not None:
                    for item in self.soubory.soubory.all():
                        item.suppress_signal = True
                        item.delete()
                    self.soubory.delete()
        except ObjectDoesNotExist as err:
            logger.debug("xml_generator.models.ModelWithMetadata.record_deletion.end", extra={"error": err})
        connector.record_deletion()
        if close_transaction is True:
            logger.debug(
                "xml_generator.models.ModelWithMetadata.save_metadata.mark_transaction_as_closed",
                extra={"transaction": getattr(fedora_transaction, "uid", "")},
            )
            fedora_transaction.mark_transaction_as_closed()

    def record_ident_change(self, old_ident_cely, fedora_transaction=None, new_ident_cely=None, delete_container=True):
        """
        Provádí operaci record ident change.

        :param old_ident_cely: Identifikátor ``old_ident_cely`` používaný pro dohledání cílového záznamu.
        :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.
        :param new_ident_cely: Identifikátor ``new_ident_cely`` používaný pro dohledání cílového záznamu.
        :param delete_container: Příznak ``delete_container`` určující průběh nebo rozsah zpracování.
        """
        if fedora_transaction is None and self.active_transaction is not None:
            fedora_transaction = self.active_transaction
        elif fedora_transaction is None and self.active_transaction is None:
            raise ValueError("No Fedora transaction")
        new_ident_cely = new_ident_cely if new_ident_cely else self.ident_cely
        logger.debug(
            "xml_generator.models.ModelWithMetadata.record_ident_change.start",
            extra={
                "transaction": fedora_transaction,
                "ident_cely_old": old_ident_cely,
                "ident_cely": new_ident_cely,
            },
        )
        from core.repository_connector import FedoraTransaction

        if not isinstance(fedora_transaction, FedoraTransaction):
            raise ValueError("fedora_transaction must be a FedoraTransaction class object")
        if (
            old_ident_cely is not None
            and isinstance(old_ident_cely, str)
            and len(old_ident_cely) > 0
            and new_ident_cely != old_ident_cely
        ):

            from core.repository_connector import FedoraRepositoryConnector

            connector = FedoraRepositoryConnector(
                self, fedora_transaction, skip_container_check=self.skip_container_check
            )
            connector.record_ident_change(old_ident_cely, delete_container)
            logger.debug(
                "cron.record_ident_change.do.end",
                extra={
                    "pk": self.pk,
                    "ident_cely_old": old_ident_cely,
                    "ident_cely": new_ident_cely,
                    "transaction": fedora_transaction.uid,
                },
            )
            from arch_z.models import ArcheologickyZaznam, ExterniOdkaz
            from dj.models import DokumentacniJednotka
            from dokument.models import Dokument, DokumentCast
            from ez.models import ExterniZdroj
            from lokalita.models import Lokalita
            from pas.models import SamostatnyNalez
            from pian.models import Pian
            from projekt.models import Projekt

            def process_arch_z(record: ArcheologickyZaznam):
                """
                               Provádí operaci process arch z.

                               :param record: Záznam, který funkce čte nebo upravuje.
                :return: Výstup funkce odpovídající implementované logice.
                """
                for inner_item in record.dokumentacni_jednotky_akce.all():
                    inner_item: DokumentacniJednotka
                    try:
                        inner_item.pian.save_metadata(fedora_transaction)
                    except (ObjectDoesNotExist, AttributeError) as err:
                        logger.debug(
                            "xml_generator.models.ModelWithMetadata.record_ident_change.process_arch_z" ".no_pian",
                            extra={"error": err},
                        )
                    try:
                        inner_item.adb.save_metadata(fedora_transaction)
                    except (ObjectDoesNotExist, AttributeError) as err:
                        logger.debug(
                            "xml_generator.models.ModelWithMetadata.record_ident_change.process_arch_z.no_adb",
                            extra={"error": err},
                        )
                for inner_item in record.casti_dokumentu.all():
                    inner_item: DokumentCast
                    inner_item.dokument.save_metadata(fedora_transaction)
                for inner_item in record.externi_odkazy.all():
                    inner_item: ExterniOdkaz
                    inner_item.externi_zdroj.save_metadata(fedora_transaction)

            if isinstance(self, ArcheologickyZaznam):
                self: ArcheologickyZaznam
                transaction.on_commit(lambda: process_arch_z(self))
            elif isinstance(self, Dokument):

                def save_metadata(record: Dokument):
                    """
                                       Uloží metadata.

                                       :param record: Záznam, který funkce čte nebo upravuje.
                    Výsledek provedené změny nad cílovým objektem.
                    """
                    for item in record.casti.all():
                        item: DokumentCast
                        if item.archeologicky_zaznam:
                            item.archeologicky_zaznam.save_metadata(fedora_transaction)
                        if item.projekt:
                            item.projekt.save_metadata(fedora_transaction)
                    if record.let:
                        record.let.save_metadata(fedora_transaction)

                self: Dokument
                transaction.on_commit(lambda: save_metadata(self))
            elif isinstance(self, ExterniZdroj):

                def save_metadata(record: ExterniZdroj):
                    """
                                       Uloží metadata.

                                       :param record: Záznam, který funkce čte nebo upravuje.
                    Výsledek provedené změny nad cílovým objektem.
                    """
                    for item in record.externi_odkazy_zdroje.all():
                        item: ExterniOdkaz
                        item.archeologicky_zaznam.save_metadata(fedora_transaction)

                self: ExterniZdroj
                transaction.on_commit(lambda: save_metadata(self))
            elif isinstance(self, Projekt):

                def save_metadata(record: Projekt):
                    """
                                       Uloží metadata.

                                       :param record: Záznam, který funkce čte nebo upravuje.
                    Výsledek provedené změny nad cílovým objektem.
                    """
                    for item in record.casti_dokumentu.all():
                        item: DokumentCast
                        item.dokument.save_metadata(fedora_transaction)
                    for item in record.samostatne_nalezy.all():
                        item: SamostatnyNalez
                        item.save_metadata(fedora_transaction)

                self: Projekt
                transaction.on_commit(lambda: save_metadata(self))
            elif isinstance(self, Lokalita):

                def save_metadata(record: Lokalita):
                    """
                                       Uloží metadata.

                                       :param record: Záznam, který funkce čte nebo upravuje.
                    Výsledek provedené změny nad cílovým objektem.
                    """
                    archeologicky_zaznam: ArcheologickyZaznam = record.archeologicky_zaznam
                    process_arch_z(archeologicky_zaznam)

                self: Lokalita
                transaction.on_commit(lambda: save_metadata(self))
            elif isinstance(self, SamostatnyNalez):

                def save_metadata(record: SamostatnyNalez):
                    """
                                       Uloží metadata.

                                       :param record: Záznam, který funkce čte nebo upravuje.
                    Výsledek provedené změny nad cílovým objektem.
                    """
                    if record.projekt:
                        record.projekt.save_metadata(fedora_transaction)

                self: SamostatnyNalez
                transaction.on_commit(lambda: save_metadata(self))
            elif isinstance(self, Pian):

                def save_metadata(record: Pian):
                    """
                                       Uloží metadata.

                                       :param record: Záznam, který funkce čte nebo upravuje.
                    Výsledek provedené změny nad cílovým objektem.
                    """
                    for item in record.dokumentacni_jednotky_pianu.all():
                        item: DokumentacniJednotka
                        item.archeologicky_zaznam.save_metadata(fedora_transaction)

                self: Pian
                save_metadata(self)

            from core.repository_connector import FedoraTransactionPostCommitTasks

            fedora_transaction.post_commit_tasks[(FedoraTransactionPostCommitTasks.CREATE_LINK, self.ident_cely)] = [
                self,
                self.ident_cely,
                old_ident_cely,
            ]
        logger.debug(
            "xml_generator.models.ModelWithMetadata.record_ident_change.end",
            extra={
                "transaction": fedora_transaction.uid,
                "ident_cely_old": old_ident_cely,
                "ident_cely": new_ident_cely,
            },
        )

    @classmethod
    def get_by_ident_cely(cls, ident_cely):
        """
        Vrací by ident cely.

        :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
        """
        try:
            return cls.objects.get(ident_cely=ident_cely)
        except Exception:
            return None

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        abstract = True
