from django.db import models


class Oznamovatel(models.Model):
    email = models.TextField()
    adresa = models.TextField()
    odpovedna_osoba = models.TextField()
    oznamovatel = models.TextField()
    telefon = models.TextField()

    def __str__(self):
        return self.odpovedna_osoba + " (" + self.email + ")"

    class Meta:
        db_table = "oznamovatel"
