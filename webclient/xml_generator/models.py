import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from celery import Celery


logger = logging.getLogger(__name__)
METADATA_UPDATE_TIMEOUT = 10
IDENT_CHANGE_UPDATE_TIMEOUT = 15


class ModelWithMetadata(models.Model):
    ident_cely = models.TextField(unique=True)
    suppress_signal = False
    soubory = None

    @property
    def metadata(self):
        from core.repository_connector import FedoraRepositoryConnector
        connector = FedoraRepositoryConnector(self)
        return connector.get_metadata()

    def save_metadata(self, use_celery=True, include_files=False):
        logger.debug("xml_generator.models.ModelWithMetadata.save_metadata.start")
        if use_celery:
            app = Celery("webclient")
            app.config_from_object("django.conf:settings", namespace="CELERY")
            app.autodiscover_tasks()
            i = app.control.inspect()
            queues = (i.scheduled(), )

            for queue in queues:
                for queue_name, queue_tasks in queue.items():
                    for task in queue_tasks:
                        if "request" in task and "save_record_metadata" in task.get("request").get("name").lower() \
                                and tuple(task.get("request").get("args")) == (self.__class__.__name__, self.pk):
                            logger.debug("xml_generator.models.ModelWithMetadata.save_metadata.already_scheduled",
                                         extra={"class_name": self.__class__.__name__, "pk": self.pk})
                            return
            from cron.tasks import save_record_metadata
            save_record_metadata.apply_async([self.__class__.__name__, self.pk], countdown=METADATA_UPDATE_TIMEOUT)
        else:
            from core.repository_connector import FedoraRepositoryConnector
            connector = FedoraRepositoryConnector(self)
            connector.save_metadata(True)
            if include_files:
                from core.models import SouborVazby
                if hasattr(self, "soubory") and isinstance(self.soubory, SouborVazby):
                    for soubor in self.soubory.soubory.all():
                        from core.models import Soubor
                        soubor: Soubor
                        connector.migrate_binary_file(soubor, include_content=False)
        logger.debug("xml_generator.models.ModelWithMetadata.save_metadata.end")

    def record_deletion(self):
        logger.debug("xml_generator.models.ModelWithMetadata.delete_repository_container.start")
        from core.repository_connector import FedoraRepositoryConnector
        connector = FedoraRepositoryConnector(self)
        try:
            from core.models import SouborVazby
            if hasattr(self, "soubory") and self.soubory is not None and isinstance(self.soubory, SouborVazby):
                for soubor in self.soubory.soubory.all():
                    from core.models import Soubor
                    soubor: Soubor
                    connector.delete_binary_file(soubor)
            logger.debug("xml_generator.models.ModelWithMetadata.delete_repository_container.end")
        except ObjectDoesNotExist as err:
            logger.debug("xml_generator.models.ModelWithMetadata.no_files_to_delete.end", extra={"err": err})
        return connector.record_deletion()

    def record_ident_change(self, old_ident_cely):
        logger.debug("xml_generator.models.ModelWithMetadata.record_ident_change.start")
        if old_ident_cely is not None:
            from cron.tasks import record_ident_change
            record_ident_change.apply_async([self.__class__.__name__, self.pk, old_ident_cely],
                                            countdown=IDENT_CHANGE_UPDATE_TIMEOUT)
        logger.debug("xml_generator.models.ModelWithMetadata.record_ident_change.end")

    class Meta:
        abstract = True
