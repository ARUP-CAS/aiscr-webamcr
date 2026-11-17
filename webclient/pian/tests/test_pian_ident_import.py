"""Testy přidělení permanentního identifikátoru PIAN v datové fázi importu (issue #391, F31).

Import zakládá PIAN pro katastrální DJ přes ``vytvor_pian`` s ``DryRunFedoraTransaction``; ``set_permanent_ident_cely``
pak volá ``record_ident_change``, které dřív tuto transakci odmítlo a import se revokoval.
"""

from unittest.mock import patch

from core.constants import PIAN_POTVRZEN
from core.repository_connector import DryRunFedoraTransaction
from django.test import TestCase
from heslar.hesla import HESLAR_PIAN_PRESNOST, HESLAR_PIAN_TYP
from heslar.models import Heslar, HeslarNazev
from pian.models import Kladyzm, Pian, PianSekvence

POLYGON_5514 = (
    "SRID=5514;POLYGON((-700000 -1000000, -700000 -1100000, -800000 -1100000, -800000 -1000000, -700000 -1000000))"
)


class PianPermanentIdentDryRunTest(TestCase):
    """``set_permanent_ident_cely`` a ``record_ident_change`` pod ``DryRunFedoraTransaction``."""

    def setUp(self):
        """Připraví hesla, klady ZM a sekvenci PIAN pro katastrální přesnost."""
        presnost_nazev, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_PIAN_PRESNOST, defaults={"nazev": "pian_presnost"}
        )
        typ_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_PIAN_TYP, defaults={"nazev": "pian_typ"})
        self.presnost = Heslar.objects.create(
            ident_cely="HES-PIANPR-F31",
            nazev_heslare=presnost_nazev,
            heslo="Katastr",
            heslo_en="Cadastre",
            zkratka="4",
            razeni=4,
        )
        self.typ = Heslar.objects.create(
            ident_cely="HES-PIANTYP-F31",
            nazev_heslare=typ_nazev,
            heslo="Plocha",
            heslo_en="Area",
            zkratka="P",
            razeni=1,
        )
        self.zm10 = Kladyzm.objects.create(cislo="F31ZM10", kategorie=10, the_geom=POLYGON_5514)
        self.zm50 = Kladyzm.objects.create(cislo="F31ZM50", kategorie=50, the_geom=POLYGON_5514)
        PianSekvence.objects.create(kladyzm50=self.zm50, sekvence=1, katastr=True)
        # Sekvence se ukládá přes samostatné spojení ``urgent``, které v testu nevidí neuložená data
        # testovací transakce; posun sekvence není předmětem testu.
        sequence_save = patch.object(PianSekvence, "save")
        sequence_save.start()
        self.addCleanup(sequence_save.stop)

    def _new_pian(self, transaction):
        """Vrátí neuložený PIAN bez identifikátoru s danou aktivní transakcí, jako ho sestaví ``vytvor_pian``."""
        pian = Pian(
            stav=PIAN_POTVRZEN,
            zm10=self.zm10,
            zm50=self.zm50,
            typ=self.typ,
            presnost=self.presnost,
            geom="SRID=4326;POINT(14.5 50.0)",
            geom_sjtsk="SRID=5514;POINT(-750000 -1050000)",
            geom_system="5514",
        )
        pian.active_transaction = transaction
        return pian

    def test_new_pian_gets_ident_and_queues_it_for_fedora_phase(self):
        """Nový PIAN pod dry-run transakcí dostane permanentní ident a ten se zařadí mezi cíle fáze Fedory."""
        transaction = DryRunFedoraTransaction()
        pian = self._new_pian(transaction)

        pian.set_permanent_ident_cely()

        self.assertTrue(pian.ident_cely.startswith("P-"), pian.ident_cely)
        self.assertIn(pian.ident_cely, transaction.updated_ident_cely)

    def test_ident_change_of_existing_container_still_requires_real_transaction(self):
        """Změnu identu záznamu s původním kontejnerem dry-run transakce dál odmítne."""
        transaction = DryRunFedoraTransaction()
        pian = self._new_pian(transaction)
        pian.set_permanent_ident_cely()

        with self.assertRaises(ValueError):
            pian.record_ident_change("P-F31-000001", fedora_transaction=transaction)
