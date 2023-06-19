from django.db import models


class ModelWithMetadata(models.Model):
    ident_cely = models.TextField(unique=True)

    @property
    def metadata(self):
        from core.repository_connector import FedoraRepositoryConnector
        connector = FedoraRepositoryConnector(self)
        return connector.get_metadata()

    def save_metadata(self):
        from core.repository_connector import FedoraRepositoryConnector
        connector = FedoraRepositoryConnector(self)
        return connector.save_metadata(True)

    class Meta:
        abstract = True
