from django.db import models


class Oznamovatel(models.Model):
    email = models.TextField()
    adresa = models.TextField()
    odpovedna_osoba = models.TextField()
    oznamovatel = models.TextField()
    telefon = models.TextField()

    class Meta:
        db_table = "oznamovatel"
