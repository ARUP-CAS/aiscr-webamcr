import logging

from django.db import models
from celery import Celery


logger = logging.getLogger(__name__)
METADATA_UPDATE_TIMEOUT = 20


class ModelWithMetadata(models.Model):
    ident_cely = models.TextField(unique=True)

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
        logger.debug("xml_generator.models.ModelWithMetadata.delete_repository_container.end")
        return connector.record_deletion()

    class Meta:
        abstract = True
