import inspect
import logging
from typing import Optional

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from celery import Celery


logger = logging.getLogger(__name__)
UPDATE_REDIS_SNAPSHOT = 20


def check_if_task_queued(class_name, pk, task_name):
    app = Celery("webclient")
    app.config_from_object("django.conf:settings", namespace="CELERY")
    app.autodiscover_tasks()
    i = app.control.inspect(["worker1@amcr"])
    queues = (i.scheduled(),)
    for queue in queues:
        for queue_name, queue_tasks in queue.items():
            for task in queue_tasks:
                if "request" in task and task_name in task.get("request").get("name").lower() \
                        and tuple(task.get("request").get("args")[:2]) == (class_name, pk):
                    logger.debug("xml_generator.models.ModelWithMetadata.check_if_task_queued.already_scheduled",
                                 extra={"class_name": class_name, "pk": pk})
                    return True
    return False


class ModelWithMetadata(models.Model):
    ident_cely = models.TextField(unique=True)
    suppress_signal = False
    soubory = None
    deleted_by_user = None
    active_transaction = None
    close_active_transaction_when_finished = False

    @property
    def metadata(self):
        from core.repository_connector import FedoraRepositoryConnector
        connector = FedoraRepositoryConnector(self)
        return connector.get_metadata()

    def container_creation_queued(self):
        from core.repository_connector import FedoraRepositoryConnector
        connector = FedoraRepositoryConnector(self)
        if not connector.container_exists() and self.update_queued(self.__class__.__name__, self.pk):
            return True
        return False

    @staticmethod
    def update_queued(class_name, pk):
        return check_if_task_queued(class_name, pk, "save_record_metadata")

    def save_metadata(self, fedora_transaction=None, include_files=False, close_transaction=False):
        from core.repository_connector import FedoraTransaction
        stack = inspect.stack()
        caller = stack[1]
        if fedora_transaction is None and self.active_transaction is not None:
            fedora_transaction = self.active_transaction
        elif fedora_transaction is None and self.active_transaction is None:
            raise ValueError("No Fedora transaction")
        if not isinstance(fedora_transaction, FedoraTransaction):
            raise ValueError("fedora_transaction must be a FedoraTransaction class object")
        if not self.ident_cely:
            logger.warning("xml_generator.models.ModelWithMetadata.save_metadata.no_ident",
                           extra={"ident_cely": self.ident_cely, "record_pk": self.pk,
                                  "record_class": self.__class__.__name__, "transaction": fedora_transaction.uid,
                                  "close_transaction": close_transaction, "caller": [f"{caller}\n"
                                                                                     for caller in stack]})
            return
        logger.debug("xml_generator.models.ModelWithMetadata.save_metadata.start",
                     extra={"ident_cely": self.ident_cely, "record_pk": self.pk,
                            "record_class": self.__class__.__name__, "transaction":
                                getattr(fedora_transaction, "uid", ""), "close_transaction": close_transaction,
                            "caller": caller})
        fedora_transaction: Optional[FedoraTransaction]
        from core.repository_connector import FedoraRepositoryConnector
        connector = FedoraRepositoryConnector(self, fedora_transaction)
        if include_files:
            from core.models import SouborVazby
            if hasattr(self, "soubory") and isinstance(self.soubory, SouborVazby):
                for soubor in self.soubory.soubory.all():
                    from core.models import Soubor
                    soubor: Soubor
                    connector.migrate_binary_file(soubor, include_content=False)
        connector.save_metadata(True)
        if close_transaction is True:
            logger.debug("xml_generator.models.ModelWithMetadata.save_metadata.mark_transaction_as_closed",
                         extra={"transaction": getattr(fedora_transaction, "uid", ""), "caller": caller})
            fedora_transaction.mark_transaction_as_closed()
        logger.debug("xml_generator.models.ModelWithMetadata.save_metadata.end",
                     extra={"transaction": getattr(fedora_transaction, "uid", ""),
                            "transaction_mark_closed": self.close_active_transaction_when_finished})

    def record_deletion(self, fedora_transaction=None, close_transaction=False):
        logger.debug("xml_generator.models.ModelWithMetadata.delete_repository_container.start")
        from arch_z.models import ArcheologickyZaznam
        from dokument.models import Dokument
        from ez.models import ExterniZdroj
        from pian.models import Pian
        from projekt.models import Projekt
        from pas.models import SamostatnyNalez

        from core.repository_connector import FedoraRepositoryConnector
        if fedora_transaction is None and self.active_transaction is not None:
            fedora_transaction = self.active_transaction
        elif fedora_transaction is None and self.active_transaction is None:
            raise ValueError("No Fedora transaction")
        from core.repository_connector import FedoraTransaction
        if not isinstance(fedora_transaction, FedoraTransaction):
            raise ValueError("fedora_transaction must be a FedoraTransaction class object")

        if isinstance(self, ArcheologickyZaznam) or isinstance(self, Dokument) or isinstance(self, ExterniZdroj)\
                or isinstance(self, Pian) or isinstance(self, Projekt) or isinstance(self, SamostatnyNalez):
            from historie.models import Historie
            Historie.save_record_deletion_record(record=self)
            self.save_metadata(fedora_transaction)
        connector = FedoraRepositoryConnector(self, fedora_transaction)
        try:
            from core.models import SouborVazby
            if hasattr(self, "soubory") and self.soubory is not None and isinstance(self.soubory, SouborVazby)\
                    and self.soubory.pk is not None:
                for soubor in self.soubory.soubory.all():
                    from core.models import Soubor
                    soubor: Soubor
                    connector.delete_binary_file(soubor)
            logger.debug("xml_generator.models.ModelWithMetadata.delete_repository_container.end")
            from dokument.models import Dokument
            from pas.models import SamostatnyNalez
            if isinstance(self, Dokument):
                if self.soubory.pk is not None:
                    self.soubory.delete()
            elif isinstance(self, SamostatnyNalez):
                if self.soubory.pk is not None:
                    self.soubory.delete()
        except ObjectDoesNotExist as err:
            logger.debug("xml_generator.models.ModelWithMetadata.no_files_to_delete.end", extra={"err": err})
        if close_transaction is True:
            logger.debug("xml_generator.models.ModelWithMetadata.save_metadata.mark_transaction_as_closed",
                         extra={"transaction": getattr(fedora_transaction, "uid", "")})
            fedora_transaction.mark_transaction_as_closed()

    def record_ident_change(self, old_ident_cely, fedora_transaction=None, new_ident_cely=None):
        if fedora_transaction is None and self.active_transaction is not None:
            fedora_transaction = self.active_transaction
        elif fedora_transaction is None and self.active_transaction is None:
            raise ValueError("No Fedora transaction")
        new_ident_cely = new_ident_cely if new_ident_cely else self.ident_cely
        logger.debug("xml_generator.models.ModelWithMetadata.record_ident_change.start",
                     extra={"transaction": fedora_transaction, "old_ident_cely": old_ident_cely,
                            "new_ident_cely": new_ident_cely})
        from core.repository_connector import FedoraTransaction
        if not isinstance(fedora_transaction, FedoraTransaction):
            raise ValueError("fedora_transaction must be a FedoraTransaction class object")
        if (old_ident_cely is not None and isinstance(old_ident_cely, str) and len(old_ident_cely) > 0
                and new_ident_cely != old_ident_cely):

            from core.repository_connector import FedoraRepositoryConnector
            connector = FedoraRepositoryConnector(self, fedora_transaction)
            connector.record_ident_change(old_ident_cely)
            logger.debug("cron.record_ident_change.do.end",
                         extra={"record_pk": self.pk, "old_ident_cely": old_ident_cely, "new_ident_cely": new_ident_cely,
                                "transaction": fedora_transaction.uid})
            from arch_z.models import ArcheologickyZaznam, ExterniOdkaz
            from dj.models import DokumentacniJednotka
            from dokument.models import DokumentCast, Dokument
            from ez.models import ExterniZdroj
            from projekt.models import Projekt
            from pian.models import Pian
            from pas.models import SamostatnyNalez
            from lokalita.models import Lokalita

            def process_arch_z(record: ArcheologickyZaznam):
                for inner_item in record.dokumentacni_jednotky_akce.all():
                    inner_item: DokumentacniJednotka
                    try:
                        inner_item.pian.save_metadata(fedora_transaction)
                    except ObjectDoesNotExist as err:
                        logger.debug("xml_generator.models.ModelWithMetadata.record_ident_change.process_arch_z"
                                     ".no_pian", extra={"err": err})
                    try:
                        inner_item.adb.save_metadata(fedora_transaction)
                    except ObjectDoesNotExist as err:
                        logger.debug("xml_generator.models.ModelWithMetadata.record_ident_change.process_arch_z.no_adb",
                                     extra={"err": err})
                for inner_item in record.casti_dokumentu.all():
                    inner_item: DokumentCast
                    inner_item.dokument.save_metadata(fedora_transaction)
                for inner_item in record.externi_odkazy.all():
                    inner_item: ExterniOdkaz
                    inner_item.externi_zdroj.save_metadata(fedora_transaction)

            if isinstance(self, ArcheologickyZaznam):
                process_arch_z(self)
            elif isinstance(self, Dokument):
                for item in self.casti.all():
                    item: DokumentCast
                    if item.archeologicky_zaznam:
                        item.archeologicky_zaznam.save_metadata(fedora_transaction)
                    if item.projekt:
                        item.projekt.save_metadata(fedora_transaction)
                if self.let:
                    self.let.save_metadata(fedora_transaction)
            elif isinstance(self, ExterniZdroj):
                for item in self.externi_odkazy_zdroje.all():
                    item: ExterniOdkaz
                    item.archeologicky_zaznam.save_metadata(fedora_transaction)
            elif isinstance(self, Projekt):
                for item in self.casti_dokumentu.all():
                    item: DokumentCast
                    item.dokument.save_metadata(fedora_transaction)
                for item in self.samostatne_nalezy.all():
                    item: SamostatnyNalez
                    item.save_metadata(fedora_transaction)
            elif isinstance(self, Lokalita):
                archeologicky_zaznam: ArcheologickyZaznam = self.archeologicky_zaznam
                process_arch_z(archeologicky_zaznam)
            elif isinstance(self, SamostatnyNalez):
                if self.projekt:
                    self.projekt.save_metadata(fedora_transaction)
            elif isinstance(self, Pian):
                for item in self.dokumentacni_jednotky_pianu.all():
                    item: DokumentacniJednotka
                    item.archeologicky_zaznam.save_metadata(fedora_transaction)
        logger.debug("xml_generator.models.ModelWithMetadata.record_ident_change.end",
                     extra={"transaction": fedora_transaction.uid, "old_ident_cely": old_ident_cely,
                            "new_ident_cely": new_ident_cely})

    class Meta:
        abstract = True
