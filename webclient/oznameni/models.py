from datetime import datetime

from django.db import models
from projekt.models import Projekt
from django_prometheus.models import ExportModelOperationsMixin


class Oznamovatel(ExportModelOperationsMixin("oznamovatel"), models.Model):
    """
    Class pro db model oznamovatel.
    """
    projekt = models.OneToOneField(
        Projekt,
        on_delete=models.CASCADE,
        related_name="oznamovatel",
        db_column="projekt",
        primary_key=True,
    )
    email = models.TextField()
    adresa = models.TextField()
    odpovedna_osoba = models.TextField()
    oznamovatel = models.TextField()
    telefon = models.TextField()

    def __str__(self):
        return self.odpovedna_osoba + " (" + self.email + ")"

    class Meta:
        db_table = "oznamovatel"
        verbose_name = "oznamovatele"

