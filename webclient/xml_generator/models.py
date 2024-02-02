import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from celery import Celery


logger = logging.getLogger(__name__)
METADATA_UPDATE_TIMEOUT = 10
IDENT_CHANGE_UPDATE_TIMEOUT = 15
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

    def save_metadata(self, transaction=None, use_celery=True, include_files=False):
        from core.repository_connector import FedoraTransaction
        transaction: FedoraTransaction
        logger.debug("xml_generator.models.ModelWithMetadata.save_metadata.start",
                     extra={"ident_cely": self.ident_cely, "use_celery": use_celery, "record_pk": self.pk,
                            "record_class": self.__class__.__name__, "transaction": transaction})
        if not transaction and self.active_transaction:
            transaction = self.active_transaction
        else:
            transaction = FedoraTransaction()
        if use_celery:
            if self.update_queued(self.__class__.__name__, self.pk):
                logger.debug("xml_generator.models.ModelWithMetadata.save_metadata.already_scheduled",
                             extra={"ident_cely": self.ident_cely, "use_celery": use_celery, "record_pk": self.pk,
                                    "record_class": self.__class__.__name__})
                return
            from cron.tasks import save_record_metadata
            save_record_metadata.apply_async([self.__class__.__name__, self.pk, transaction.uid],
                                             countdown=METADATA_UPDATE_TIMEOUT)
        else:
            from core.repository_connector import FedoraRepositoryConnector
            connector = FedoraRepositoryConnector(self, transaction.uid)
            if include_files:
                from core.models import SouborVazby
                if hasattr(self, "soubory") and isinstance(self.soubory, SouborVazby):
                    for soubor in self.soubory.soubory.all():
                        from core.models import Soubor
                        soubor: Soubor
                        connector.migrate_binary_file(soubor, include_content=False)
            connector.save_metadata(True)
        logger.debug("xml_generator.models.ModelWithMetadata.save_metadata.end", extra={"transaction": transaction})
        return transaction

    def record_deletion(self, transaction=None):
        logger.debug("xml_generator.models.ModelWithMetadata.delete_repository_container.start")
        from arch_z.models import ArcheologickyZaznam
        from dokument.models import Dokument
        from ez.models import ExterniZdroj
        from pian.models import Pian
        from projekt.models import Projekt
        from pas.models import SamostatnyNalez
        if isinstance(self, ArcheologickyZaznam) or isinstance(self, Dokument) or isinstance(self, ExterniZdroj)\
                or isinstance(self, Pian) or isinstance(self, Projekt) or isinstance(self, SamostatnyNalez):
            from historie.models import Historie
            Historie.save_record_deletion_record(record=self)
            self.save_metadata(use_celery=False)
        from core.repository_connector import FedoraRepositoryConnector
        if not transaction and self.active_transaction:
            transaction = self.active_transaction
        else:
            from core.repository_connector import FedoraTransaction
            transaction = FedoraTransaction()
        connector = FedoraRepositoryConnector(self, transaction)
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
        return transaction

    def record_ident_change(self, old_ident_cely, transaction=None):
        logger.debug("xml_generator.models.ModelWithMetadata.record_ident_change.start",
                     extra={"transaction": transaction})
        if (old_ident_cely is not None and isinstance(old_ident_cely, str) and len(old_ident_cely) > 0
                and self.ident_cely != old_ident_cely):
            from cron.tasks import record_ident_change
            if not transaction:
                record_ident_change.apply_async([self.__class__.__name__, self.pk, old_ident_cely],
                                                countdown=IDENT_CHANGE_UPDATE_TIMEOUT)
            else:
                record_ident_change.apply_async([self.__class__.__name__, self.pk, old_ident_cely, transaction.uid],
                                                countdown=IDENT_CHANGE_UPDATE_TIMEOUT)
        logger.debug("xml_generator.models.ModelWithMetadata.record_ident_change.end",
                     extra={"transaction": transaction})

    class Meta:
        abstract = True
