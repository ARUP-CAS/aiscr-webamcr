from datetime import datetime

from django.db import models
from projekt.models import Projekt


class Oznamovatel(models.Model):
    projekt = models.OneToOneField(
        Projekt,
        on_delete=models.CASCADE,
        related_name="oznamovatel",
        db_column="projekt",
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

    def set_dummy_data(self, projekt):
        value = "Údaj nezadán"
        self.projekt = projekt
        self.oznamovatel = value
        self.odpovedna_osoba = value
        self.adresa = value
        self.telefon = value
        self.email = value

    def remove_data(self):
        value = "Údaj odstraněn (" + str(datetime.today().date()) + ")"
        self.oznamovatel = value
        self.odpovedna_osoba = value
        self.adresa = value
        self.telefon = value
        self.email = value
        self.save()
