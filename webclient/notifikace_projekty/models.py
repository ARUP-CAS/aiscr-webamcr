from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django_prometheus.models import ExportModelOperationsMixin
from uzivatel.models import User


class Pes(ExportModelOperationsMixin("pes"), models.Model):
    """
    Databázový model hlídacího psa.
    """

    user = models.ForeignKey(User, models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now=True)

    @property
    def ident_cely(self):
        """Provádí operaci ident cely.

        :return: Vrací výsledek provedené operace."""
        return getattr(self.content_object, "ident_cely", None)

    def __str__(self):
        """Vrací textovou reprezentaci objektu.

        :return: Vrací výsledek provedené operace."""
        return str(self.content_object)

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
        db_table = "notifikace_projekty_pes"
        constraints = [
            models.UniqueConstraint(fields=["user", "content_type", "object_id"], name="unique_pes"),
        ]

    def get_create_user(self):
        """Vrací create user.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        return (self.user,)
