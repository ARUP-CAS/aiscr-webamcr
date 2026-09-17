"""
Testy determinismu pořadí prvků v generovaných XML metadatech.

Pokrývají :func:`xml_generator.generator.stable_related_records`, která doplňuje primární klíč
jako poslední kritérium řazení navázaných záznamů. Bez něj PostgreSQL vrací řádky se shodným
řadicím klíčem v libovolném pořadí a tentýž nezměněný záznam generuje odlišné XML, což vede
ke vzniku zbytečných verzí v OCFL úložišti.
"""

from core.models import Soubor
from django.test import SimpleTestCase
from historie.models import Historie
from xml_generator.generator import stable_related_records


class StableRelatedRecordsTest(SimpleTestCase):
    """Testuje doplnění stabilního řazení navázaných záznamů."""

    def test_doplni_pk_k_nejednoznacnemu_razeni(self):
        """Model řazený podle neunikátního pole dostane ``pk`` jako poslední kritérium."""
        queryset = stable_related_records(Historie.objects)
        self.assertEqual(list(queryset.query.order_by), ["datum_zmeny", "pk"])

    def test_zachova_existujici_razeni_modelu(self):
        """Původní řadicí kritéria modelu zůstanou zachována i s doplněným tiebreakerem."""
        queryset = stable_related_records(Historie.objects)
        self.assertEqual(list(queryset.query.order_by)[:-1], list(Historie._meta.ordering))

    def test_nepridava_pk_kdyz_uz_razeni_obsahuje_id(self):
        """Řazení, které už obsahuje ``id``, je jednoznačné a nepotřebuje další kritérium."""
        queryset = stable_related_records(Soubor.objects)
        self.assertEqual(list(Soubor._meta.ordering), ["nazev", "id"])
        self.assertEqual(list(queryset.query.order_by), [])

    def test_respektuje_razeni_nastavene_na_querysetu(self):
        """Explicitní ``order_by`` na QuerySetu má přednost před výchozím řazením modelu."""
        queryset = stable_related_records(Soubor.objects.order_by("-mimetype"))
        self.assertEqual(list(queryset.query.order_by), ["-mimetype", "pk"])

    def test_objekt_bez_querysetu_projde_beze_zmeny(self):
        """Kolekce, která není QuerySet, se vrátí beze změny a nezpůsobí chybu."""

        class _Kolekce:
            """Náhrada za manažer relace vracející prostý seznam."""

            @staticmethod
            def all():
                """
                Vrátí položky kolekce.

                :return: Seznam položek bez vazby na databázi.
                """
                return ["a", "b"]

        self.assertEqual(stable_related_records(_Kolekce()), ["a", "b"])


class SouborOrderingTest(SimpleTestCase):
    """Testuje jednoznačnost výchozího řazení modelu :class:`core.models.Soubor`."""

    def test_razeni_obsahuje_tiebreaker(self):
        """``nazev`` není unikátní, proto musí řazení končit primárním klíčem."""
        self.assertEqual(list(Soubor._meta.ordering), ["nazev", "id"])
