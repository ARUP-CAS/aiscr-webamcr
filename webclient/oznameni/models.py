from django.db import models
from django_prometheus.models import ExportModelOperationsMixin
from projekt.models import Projekt


class Oznamovatel(ExportModelOperationsMixin("oznamovatel"), models.Model):
    """
    Databázový model oznamovatele.
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
    poznamka = models.CharField(max_length=1000, null=True, blank=True)

    def __str__(self):
        """Funkce `Oznamovatel.__str__` v modulu `webclient.oznameni.models`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        return self.odpovedna_osoba + " (" + self.email + ")"

    class Meta:
        """Třída `Oznamovatel.Meta` v modulu `webclient.oznameni.models`.
        
        Zapouzdřuje související data a chování v rámci dané části aplikace.
        """
        db_table = "oznamovatel"
        verbose_name = "oznamovatele"
