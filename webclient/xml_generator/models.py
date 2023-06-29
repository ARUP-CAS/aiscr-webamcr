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

    def save_metadata(self):
        logger.debug("xml_generator.models.ModelWithMetadata.save_metadata")
        app = Celery("webclient")
        app.config_from_object("django.conf:settings", namespace="CELERY")
        app.autodiscover_tasks()
        i = app.control.inspect()
        queues = (i.scheduled(), i.active())

        for queue in queues:
            print(queue.items())
            for queue_name, queue_tasks in queue.items():
                for task in queue_tasks:
                    if "save_record_metadata" in task.get("request").get("name").lower() \
                            and tuple(task.get("request").get("args")) == (self.__class__.__name__, self.pk):
                        logger.debug("xml_generator.models.ModelWithMetadata.already_scheduled",
                                     extra={"class_name": self.__class__.__name__, "pk": self.pk})
                        return
        from cron.tasks import save_record_metadata
        save_record_metadata.apply_async([self.__class__.__name__, self.pk], countdown=METADATA_UPDATE_TIMEOUT)
        logger.debug("xml_generator.models.ModelWithMetadata.end")

    class Meta:
        abstract = True
