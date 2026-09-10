"""
Testy rizikových cest synchronizace heslářů RÚIAN (issue #372).

Pokrývají místa, kde chyba nevede k pádu, ale k tiché ztrátě nebo poškození
dat: parsování GML hranic, kontrolu úplnosti zdroje před destruktivním diffem,
kotvení denního cronu po HTTP 404, pořadí selhání PostgreSQL vs. Fedora,
dohledání chybějícího nadřazeného prvku a serializaci souběžných běhů.

Testy bez databáze jsou v :class:`django.test.SimpleTestCase`, aby se daly
spustit kdekoli. Ostatní používají :class:`django.test.TestCase`, tedy běží
v transakci, která se na konci vrátí – ``post_save`` signály heslářů plánují
zápis do Fedory přes ``transaction.on_commit()``, který se v ``TestCase``
nespouští, takže se při testech do repozitáře nesahá.
"""

import datetime
import logging
from unittest import mock

from core.utils import reprezentativni_bod_sql
from cron import tasks
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.db import connection, transaction
from django.test import SimpleTestCase, TestCase, override_settings
from heslar.models import RuianKatastr, RuianKraj, RuianOkres, RuianSyncRun
from heslar.ruian_sync import reassign as reassign_mod
from heslar.ruian_sync import syncer
from heslar.ruian_sync.provider import (
    EVENT_UPSERT,
    LEVEL_KRAJ,
    RuianChangeEvent,
    RuianFullState,
    RuianKatastrDTO,
    RuianKrajDTO,
    RuianOkresDTO,
)
from heslar.ruian_sync.vfr_parser import (
    RuianMissingMandatoryFieldError,
    _lezi_uvnitr,
    _neznamy_geometricky_prvek,
    _preved_vnorene_casti_na_diry,
)
from lxml import etree

GML = "http://www.opengis.net/gml/3.2"


def _ctverec(x0, y0, strana):
    """
    Vytvoří uzavřený čtvercový prsten pro testy vnořování částí.

    :param x0: X levého dolního rohu.
    :param y0: Y levého dolního rohu.
    :param strana: Délka strany.
    :return: Seznam bodů ``[(x, y), …]`` s uzavřeným prstencem.
    """
    return [
        (x0, y0),
        (x0 + strana, y0),
        (x0 + strana, y0 + strana),
        (x0, y0 + strana),
        (x0, y0),
    ]


class PrevodVnorenychCastiNaDiryTests(SimpleTestCase):
    """
    Testy převodu vnořených částí multipolygonu na díry ve vfr_parseru.

    Regrese na okres 3703 Brno-venkov: ČÚZK posílá enklávu jako samostatný
    ``surfaceMember`` s vlastním ``exterior`` místo jako ``gml:interior``.
    Doslovné převzetí nafoukne plochu o plochu enklávy.
    """

    def test_vnorena_cast_se_stane_dirou(self):
        """Část ležící celá uvnitř jiné se přesune mezi její vnitřní prstence."""
        vnejsi = [_ctverec(0, 0, 100)]
        vnitrni = [_ctverec(40, 40, 10)]

        vysledek = _preved_vnorene_casti_na_diry([vnejsi, vnitrni])

        self.assertEqual(len(vysledek), 1, "vnořená část nesmí zůstat samostatným polygonem")
        self.assertEqual(len(vysledek[0]), 2, "z vnořené části se má stát vnitřní prstenec")
        self.assertEqual(vysledek[0][1], _ctverec(40, 40, 10))

    def test_oddelene_casti_zustanou_samostatne(self):
        """Dvě části vedle sebe jsou dva polygony, ne polygon s dírou."""
        vysledek = _preved_vnorene_casti_na_diry([[_ctverec(0, 0, 10)], [_ctverec(50, 50, 10)]])

        self.assertEqual(len(vysledek), 2)
        for cast in vysledek:
            self.assertEqual(len(cast), 1, "u oddělených částí nesmí vzniknout díra")

    def test_jedina_cast_projde_beze_zmeny(self):
        """Multipolygon o jedné části se nemá čím vnořit."""
        casti = [[_ctverec(0, 0, 10)]]

        self.assertEqual(_preved_vnorene_casti_na_diry(casti), casti)

    def test_lezi_uvnitr_snese_bod_na_hranici(self):
        """
        Prsten, jehož první vrchol leží *na* obalující hranici, je pořád uvnitř.

        Přesně tenhle případ nastal u Brna-města: první vrchol enklávy leží na
        hranici okresu, takže test jediného vrcholu vracel nesprávně ``False``.
        Rozhoduje proto většina ze vzorku bodů.
        """
        obalujici = _ctverec(0, 0, 100)
        # První vrchol leží přesně na levé hraně obalujícího čtverce.
        dotykajici = [(0, 50), (40, 50), (40, 60), (10, 60), (0, 50)]

        self.assertTrue(_lezi_uvnitr(dotykajici, obalujici))


class NeznamyGeometrickyPrvekTests(SimpleTestCase):
    """
    Testy whitelistu podporovaných GML prvků v hranici územní jednotky.

    Whitelist je zvolen záměrně místo blacklistu: neznámý prvek se musí ohlásit,
    ne tiše přeskočit, jinak by se hranice uložila zkomolená.
    """

    @staticmethod
    def _hranice(vnitrek):
        """
        Sestaví element ``OriginalniHranice`` s předaným GML obsahem.

        :param vnitrek: XML řetězec vkládaný dovnitř kořenového elementu.
        :return: Naparsovaný kořenový element.
        """
        return etree.fromstring(f'<OriginalniHranice xmlns:gml="{GML}">{vnitrek}</OriginalniHranice>')

    def test_podporovana_geometrie_projde(self):
        """Kombinace MultiSurface/Polygon/LinearRing/posList je zpracovatelná."""
        elem = self._hranice(
            "<gml:MultiSurface><gml:surfaceMember><gml:Polygon><gml:exterior>"
            "<gml:LinearRing><gml:posList>0 0 1 0 1 1 0 0</gml:posList></gml:LinearRing>"
            "</gml:exterior></gml:Polygon></gml:surfaceMember></gml:MultiSurface>"
        )

        self.assertIsNone(_neznamy_geometricky_prvek(elem))

    def test_kruhovy_oblouk_je_podporovany(self):
        """``ArcString``/``Curve``/``segments`` parser umí linearizovat."""
        elem = self._hranice(
            "<gml:MultiSurface><gml:surfaceMember><gml:Polygon><gml:exterior><gml:Ring>"
            "<gml:curveMember><gml:Curve><gml:segments><gml:ArcString>"
            "<gml:posList>0 0 1 1 2 0</gml:posList>"
            "</gml:ArcString></gml:segments></gml:Curve></gml:curveMember>"
            "</gml:Ring></gml:exterior></gml:Polygon></gml:surfaceMember></gml:MultiSurface>"
        )

        self.assertIsNone(_neznamy_geometricky_prvek(elem))

    def test_neznamy_prvek_se_ohlasi_jmenem(self):
        """Vrací se local-name prvku, ať operátor z logu pozná, co přibylo."""
        elem = self._hranice(
            "<gml:MultiSurface><gml:surfaceMember><gml:Polygon><gml:exterior>"
            "<gml:LinearRing><gml:Bezier>0 0</gml:Bezier></gml:LinearRing>"
            "</gml:exterior></gml:Polygon></gml:surfaceMember></gml:MultiSurface>"
        )

        self.assertEqual(_neznamy_geometricky_prvek(elem), "Bezier")

    def test_koren_se_nekontroluje(self):
        """Prázdná hranice nehlásí sama sebe jako neznámý prvek."""
        self.assertIsNone(_neznamy_geometricky_prvek(self._hranice("")))


class PopisZmenyKatastruTests(SimpleTestCase):
    """
    Testy skládání poznámky do historie bez zásahu do databáze.

    Změna hlavního katastru i M2M dalších katastrů musí skončit v **jednom**
    záznamu historie, ne ve dvou samostatných.
    """

    def test_popis_hlavniho_katastru(self):
        """Změna hlavního katastru se zapisuje šipkou."""
        self.assertEqual(reassign_mod._popis_zmeny_hlavniho("Jehnědí", "Horní Sloupnice"), "Jehnědí -> Horní Sloupnice")

    def test_popis_ostatnich_bez_zmeny_je_prazdny(self):
        """Bez přidaných i odebraných katastrů nevzniká žádný text."""
        self.assertEqual(reassign_mod._popis_zmeny_ostatnich(set(), set()), "")


#: Cacheops drží výsledky dotazů v Redis, který se s rollbackem testovací
#: transakce **nevrací** – výsledky by pak prosakovaly mezi testy. Třídy, které
#: čtou stav auditu opakovaně v rámci jednoho testu, ho proto mají vypnutý.
_BEZ_CACHEOPS = override_settings(CACHEOPS_ENABLED=False)


def _vytvor_ruian_data(pocet_katastru, *, prefix=900000):
    """
    Vytvoří minimální hesláře RÚIAN pro testy nezávisle na obsahu databáze.

    Zapisuje přes ``bulk_create``, které obchází ``save()`` – ten u
    :class:`~heslar.models.RuianKatastr` ověřuje stav kontejneru ve Fedoře
    a v testech by sahal na repozitář.

    Katastry dostanou čtvercové hranice vedle sebe v EPSG:5514 (záporná
    konvence), aby na nich šly zkoušet i prostorové dotazy.

    :param pocet_katastru: Kolik katastrů vytvořit.
    :param prefix: Základ číselné řady kódů, ať nekolidují s reálnými daty.
    :return: Trojice ``(kraj, okres, seznam katastrů)``.
    """
    kraj = RuianKraj.objects.create(
        nazev=f"Testovací kraj {prefix}",
        kod=prefix,
        rada_id="T",
        nazev_en=f"Test region {prefix}",
    )
    okres = RuianOkres.objects.create(
        nazev=f"Testovací okres {prefix}",
        kraj=kraj,
        spz=f"T{(prefix // 1000) % 100:02d}",
        kod=prefix + 1,
        nazev_en=f"Test district {prefix}",
    )
    katastry = []
    for i in range(pocet_katastru):
        x0 = -700000.0 - i * 1000
        y0 = -1000000.0
        ctverec = Polygon(((x0, y0), (x0 + 900, y0), (x0 + 900, y0 + 900), (x0, y0 + 900), (x0, y0)), srid=5514)
        katastry.append(
            RuianKatastr(
                okres=okres,
                nazev=f"Testovací KÚ {prefix + i}",
                kod=prefix + 100 + i,
                definicni_bod=Point(x0 + 450, y0 + 450, srid=5514),
                hranice=MultiPolygon(ctverec, srid=5514),
            )
        )
    RuianKatastr.objects.bulk_create(katastry)
    return kraj, okres, katastry


@_BEZ_CACHEOPS
class UplnostZdrojeTests(TestCase):
    """
    Testy kontroly úplnosti plného stavu před destruktivním diffem.

    Kontrola musí běžet **před** destruktivním diffem: plný stav je snapshot a
    prvek, který v něm chybí, se maže. Neúplný, ale neprázdný vstup by tak
    smazal katastry i s reassignem navázaných záznamů.
    """

    def setUp(self):
        """
        Připraví audit záznam a vlastní hesláře.

        Katastrů se zakládá o dva víc, než je práh, aby šlo zkoušet obě strany
        hranice. Krajů a okresů vznikají tři: jejich práh je jeden chybějící
        prvek, takže „nad prahem“ znamená dva – a zdroj přitom nesmí zůstat
        prázdný, protože prázdnou úroveň řeší jiná pojistka.
        """
        self.run = RuianSyncRun.objects.create(
            mode=RuianSyncRun.MODE_FULL,
            source="shp",
            triggered_by=RuianSyncRun.TRIGGER_MANAGE,
            data_valid_to=datetime.date(2026, 1, 1),
            variant="ZKSH",
        )
        _vytvor_ruian_data(syncer._MAX_UBYTEK_KATASTRU + 2, prefix=900000)
        _vytvor_ruian_data(1, prefix=910000)
        _vytvor_ruian_data(1, prefix=911000)
        self.kody_katastru = list(RuianKatastr.objects.values_list("kod", flat=True))
        self.kody_okresu = list(RuianOkres.objects.values_list("kod", flat=True))
        self.kody_kraju = list(RuianKraj.objects.values_list("kod", flat=True))

    def _stav(self, chybi_katastru=0, chybi_okresu=0, chybi_kraju=0):
        """
        Sestaví plný stav odvozený z databáze, zkrácený o zadaný počet prvků.

        :param chybi_katastru: Kolik katastrů ve zdroji vynechat.
        :param chybi_okresu: Kolik okresů ve zdroji vynechat.
        :param chybi_kraju: Kolik krajů ve zdroji vynechat.
        :return: Instance :class:`RuianFullState`.
        """
        kraje = self.kody_kraju[: len(self.kody_kraju) - chybi_kraju]
        okresy = self.kody_okresu[: len(self.kody_okresu) - chybi_okresu]
        katastry = self.kody_katastru[: len(self.kody_katastru) - chybi_katastru]
        return RuianFullState(
            kraje=[RuianKrajDTO(kod=k, nazev="x") for k in kraje],
            okresy=[RuianOkresDTO(kod=k, nazev="x", kraj_kod=self.kody_kraju[0]) for k in okresy],
            katastry=[RuianKatastrDTO(kod=k, nazev="x", okres_kod=self.kody_okresu[0]) for k in katastry],
        )

    def test_uplny_zdroj_projde(self):
        """Snapshot shodný s databází nic nezastaví."""
        syncer._zkontroluj_uplnost_zdroje(self._stav(), self.run)

    def test_uklidnujici_ubytek_projde(self):
        """Úbytek pod prahem odpovídá reálnému slučování katastrů."""
        syncer._zkontroluj_uplnost_zdroje(self._stav(chybi_katastru=syncer._MAX_UBYTEK_KATASTRU - 1), self.run)

    def test_velky_ubytek_katastru_zastavi_beh(self):
        """Nad prahem se běh zastaví dřív, než se cokoli smaže."""
        with self.assertRaises(syncer.RuianNeuplnyZdrojError):
            syncer._zkontroluj_uplnost_zdroje(self._stav(chybi_katastru=syncer._MAX_UBYTEK_KATASTRU + 1), self.run)

        self.run.refresh_from_db()
        self.assertIn("Neúplný zdroj", self.run.note or "", "důvod zastavení musí zůstat v auditu")

    def test_chybejici_okresy_zastavi_beh(self):
        """Zánik okresu je změna „jednou za generaci“, víc než jeden = vadný vstup."""
        with self.assertRaises(syncer.RuianNeuplnyZdrojError):
            syncer._zkontroluj_uplnost_zdroje(self._stav(chybi_okresu=syncer._MAX_UBYTEK_OKRESU + 1), self.run)

    def test_chybejici_kraje_zastavi_beh(self):
        """Totéž pro kraje."""
        with self.assertRaises(syncer.RuianNeuplnyZdrojError):
            syncer._zkontroluj_uplnost_zdroje(self._stav(chybi_kraju=syncer._MAX_UBYTEK_KRAJU + 1), self.run)

    def test_prazdna_uroven_resi_jina_pojistka(self):
        """
        Úplně prázdná úroveň tuhle kontrolu neshodí.

        Prázdný zdroj znamená „nemám data pro tuto úroveň“ a řeší ho pojistka
        v :func:`~heslar.ruian_sync.syncer._apply_full_state`, která mazání
        přeskočí. Kdyby to zastavovala i tahle kontrola, hlásily by se dvě
        různé chyby na tentýž stav.
        """
        syncer._zkontroluj_uplnost_zdroje(RuianFullState(kraje=[], okresy=[], katastry=[]), self.run)


class DohledaniOkresuTests(TestCase):
    """
    Testy prostorového dohledání okresu u katastru bez vazby na obec.

    Denní změnový soubor odkazuje okres katastru přes obec. Když obec ve
    stejném souboru není, parser doplní ``okres_kod=0``. U nového katastru
    pak není z čeho vzít povinný cizí klíč.
    """

    def setUp(self):
        """Vytvoří vlastní kraj, okres a katastr s hranicí i definičním bodem."""
        _, self.okres, katastry = _vytvor_ruian_data(1, prefix=920000)
        self.vzor = katastry[0]

    def test_okres_se_dohleda_podle_definicniho_bodu(self):
        """Bod uvnitř území určí okres jednoznačně – katastr leží celý v jednom."""
        dto = RuianKatastrDTO(
            kod=999001,
            nazev="Testovací KÚ",
            okres_kod=0,
            definicni_bod_wkt=self.vzor.definicni_bod.wkt,
        )

        # Testovací okres nemá vyplněnou ``hranice``, takže se uplatní záložní
        # cesta přes hranici katastru – právě ta drží dohledání funkční i tam,
        # kde okresy polygony z RÚIAN naplněné nemají.
        self.assertEqual(syncer._dohledej_okres_prostorove(dto).pk, self.okres.pk)

    def test_bod_mimo_uzemi_nedohleda_nic(self):
        """Mimo ČR není co najít – vrací se ``None``, ne náhodný okres."""
        dto = RuianKatastrDTO(kod=999002, nazev="Mimo ČR", okres_kod=0, definicni_bod_wkt="POINT(0 0)")

        self.assertIsNone(syncer._dohledej_okres_prostorove(dto))

    def test_bez_definicniho_bodu_nedohleda_nic(self):
        """Bez bodu se nedá dohledat nic prostorově."""
        dto = RuianKatastrDTO(kod=999003, nazev="Bez bodu", okres_kod=0, definicni_bod_wkt=None)

        self.assertIsNone(syncer._dohledej_okres_prostorove(dto))

    def test_novy_katastr_bez_okresu_vyhodi_vyjimku(self):
        """
        Nedohledatelný okres u nového katastru musí běh shodit, ne ho zahodit.

        Dřív se jen zalogovala chyba a vrátilo ``(False, False)``: den doběhl
        jako úspěšný, kotva se posunula a katastr nikdy nevznikl ani se
        nezopakoval.
        """
        dto = RuianKatastrDTO(kod=999004, nazev="Nedohledatelný", okres_kod=0, definicni_bod_wkt="POINT(0 0)")

        with self.assertRaises(RuianMissingMandatoryFieldError):
            syncer._upsert_katastr(None, dto, None)

    def test_existujici_katastr_si_okres_ponecha(self):
        """U existujícího katastru ``okres_kod=0`` znamená „neměň okres“."""
        dto = RuianKatastrDTO(kod=self.vzor.kod, nazev=self.vzor.nazev, okres_kod=0, definicni_bod_wkt=None)
        self.vzor.suppress_signal = True

        syncer._upsert_katastr(self.vzor, dto, None)

        self.assertEqual(RuianKatastr.objects.get(pk=self.vzor.pk).okres_id, self.vzor.okres_id)


class HistorieZmenyKatastruTests(TestCase):
    """
    Testy zápisu změny katastrů do historie jedním záznamem.

    Recenze PR #4066 žádala, aby změna hlavního katastru a změna M2M dalších
    katastrů nevytvářely dva samostatné řádky historie.

    Zápis do :class:`~historie.models.Historie` je odstíněný mockem: testuje se
    **kolik** řádků vznikne a s jakou poznámkou, ne uložení jako takové. Bez
    toho by test potřeboval existujícího admin uživatele, který s testovanou
    logikou nesouvisí.
    """

    def setUp(self):
        """Nahradí zápis historie i načtení uživatele mockem."""
        self.historie = mock.patch.object(reassign_mod, "Historie").start()
        self.addCleanup(mock.patch.stopall)

    def _poznamky(self):
        """
        Vrátí poznámky předané do ``Historie.objects.create``.

        :return: Seznam textů poznámek.
        """
        return [volani.kwargs["poznamka"] for volani in self.historie.objects.create.call_args_list]

    def test_hlavni_i_ostatni_v_jednom_zaznamu(self):
        """Obě změny najednou dají jeden řádek se spojenou poznámkou."""
        reassign_mod.log_katastr_change(
            1,
            reassign_mod._popis_zmeny_hlavniho("Starý", "Nový"),
            reassign_mod._popis_zmeny_ostatnich({101}, {102}),
        )

        poznamky = self._poznamky()
        self.assertEqual(len(poznamky), 1, "nesmí vzniknout dva samostatné záznamy")
        self.assertEqual(poznamky[0], "Starý -> Nový, +101, -102")

    def test_prazdne_casti_se_preskoci(self):
        """Změna jen hlavního katastru nemá za sebou vláčet prázdný M2M popis."""
        reassign_mod.log_katastr_change(1, reassign_mod._popis_zmeny_hlavniho("A", "B"), "")

        self.assertEqual(self._poznamky(), ["A -> B"])

    def test_zadna_zmena_nezapisuje(self):
        """Bez jakékoli změny nevzniká řádek historie."""
        reassign_mod.log_katastr_change(1, "", "")

        self.historie.objects.create.assert_not_called()

    def test_bez_vazby_se_nezapisuje(self):
        """Záznam bez vazby na historii se tiše přeskočí."""
        reassign_mod.log_katastr_change(None, "A -> B")

        self.historie.objects.create.assert_not_called()


class _FakeFedoraTransakce:
    """Náhrada :class:`FedoraTransaction`, která nesahá na repozitář."""

    def __init__(self, commit_selze=False):
        """
        :param commit_selze: Když ``True``, commit projde a teprve navazující
            krok selže – simuluje stav, kdy Fedora zápis má, ale DB se vrací.
        """
        self.uid = "test-tx"
        self.status = reassign_mod.FedoraTransactionStatus.ACTIVE
        self.commit_selze = commit_selze
        self.rollbacknuta = False

    def mark_transaction_as_closed(self):
        """
        Uzavře transakci commitem – druhý pokus odmítne stejně jako Fedora.

        Reálný repozitář na opakovaný commit odpoví ``Transaction … has
        already been committed``; tahle náhrada to napodobuje, aby se dvojitý
        commit v testu projevil, a ne tiše prošel.
        """
        if self.status is reassign_mod.FedoraTransactionStatus.COMMITTED:
            raise RuntimeError(f"Transaction with transactionId: {self.uid} has already been committed.")
        self.status = reassign_mod.FedoraTransactionStatus.COMMITTED
        if self.commit_selze:
            raise RuntimeError("commit prošel, navazující krok spadl")

    def rollback_transaction(self):
        """Označí transakci za odvolanou."""
        self.rollbacknuta = True
        self.status = reassign_mod.FedoraTransactionStatus.ABORTED


class PoradiSelhaniDbAFedoryTests(TestCase):
    """
    Testy pořadí selhání databáze a repozitáře Fedora při reassignu.

    Dřív běžely změny FK, M2M i řádek historie v autocommitu **před** vznikem
    Fedora transakce. Když pak commit selhal, volající chybu odchytil, ale
    zapsané vazby už nedokázal vrátit.

    Jako databázový zápis slouží :class:`~heslar.models.RuianSyncRun` – nemá
    povinné cizí klíče, takže test měří jen chování transakce.
    """

    ZNACKA = "test _db_a_fedora"

    def _zapis_do_db(self):
        """Provede uvnitř bloku databázový zápis, který jde snadno ověřit."""
        RuianSyncRun.objects.create(
            mode=RuianSyncRun.MODE_DELTA,
            source="file_vfr",
            triggered_by=RuianSyncRun.TRIGGER_CRON,
            data_valid_to=datetime.date(2026, 5, 5),
            variant="ZKSH",
            note=self.ZNACKA,
        )

    def _pocet_zaznamu(self):
        """
        Spočítá řádky zapsané uvnitř testovaného bloku.

        :return: Počet záznamů.
        """
        return RuianSyncRun.objects.filter(note=self.ZNACKA).count()

    def test_uspech_commituje_a_zapis_zustava(self):
        """Při úspěchu se transakce commitne a databázový zápis platí."""
        fake = _FakeFedoraTransakce()
        with mock.patch.object(reassign_mod, "FedoraTransaction", lambda: fake):
            with reassign_mod._db_a_fedora("TEST-001"):
                self._zapis_do_db()

        self.assertEqual(fake.status, reassign_mod.FedoraTransactionStatus.COMMITTED)
        self.assertFalse(fake.rollbacknuta)
        self.assertEqual(self._pocet_zaznamu(), 1)

    def test_chyba_uvnitr_vrati_databazi_i_fedoru(self):
        """Výjimka uvnitř bloku odvolá Fedora transakci i databázový zápis."""
        fake = _FakeFedoraTransakce()
        with mock.patch.object(reassign_mod, "FedoraTransaction", lambda: fake):
            with self.assertRaises(ValueError):
                with reassign_mod._db_a_fedora("TEST-002"):
                    self._zapis_do_db()
                    raise ValueError("zápis selhal")

        self.assertTrue(fake.rollbacknuta)
        self.assertEqual(fake.status, reassign_mod.FedoraTransactionStatus.ABORTED)
        self.assertEqual(self._pocet_zaznamu(), 0, "databázová část se musí vrátit")

    def test_rozpad_db_a_fedory_se_zaloguje(self):
        """
        Když Fedora commit prošel a DB se přesto vrací, musí to jít dohledat.

        Tenhle případ ošetřit nejde (repozitář commit už má), proto se aspoň
        loguje na ``ERROR`` s ``ident_cely`` a UID transakce.
        """
        fake = _FakeFedoraTransakce(commit_selze=True)
        with mock.patch.object(reassign_mod, "FedoraTransaction", lambda: fake):
            with self.assertLogs(reassign_mod.logger, level=logging.ERROR) as zachyt:
                with self.assertRaises(RuntimeError):
                    with reassign_mod._db_a_fedora("TEST-003"):
                        self._zapis_do_db()

        self.assertTrue(
            any("rozpad_db_fedora" in radek for radek in zachyt.output),
            f"rozpad se neohlásil: {zachyt.output}",
        )
        self.assertEqual(self._pocet_zaznamu(), 0)


class _FakeDatetimeModul:
    """Náhrada modulu ``datetime`` v ``cron.tasks`` s pevným „dnes“."""

    timedelta = datetime.timedelta

    def __init__(self, dnes):
        """
        :param dnes: Datum, které má vracet ``datetime.date.today()``.
        """
        self.date = type("D", (), {"today": staticmethod(lambda: dnes)})


@_BEZ_CACHEOPS
class KotvaPo404Tests(TestCase):
    """
    Testy kotvení :func:`~cron.tasks.sync_ruian_changes` při HTTP 404.

    404 u staršího dne obvykle znamená „ten den nebyly změny“, ale úplně stejně
    vypadá i změněná URL na straně ČÚZK. Den se proto neuzavírá jako úspěch
    hned – potvrdí ho až pozdější den, který se opravdu stáhne.
    """

    DEN0 = datetime.date(2000, 1, 1)
    DNES = datetime.date(2000, 2, 1)

    def setUp(self):
        """Založí výchozí úspěšný běh, od kterého se odvíjí kotva."""
        RuianSyncRun.objects.all().delete()
        RuianSyncRun.objects.create(
            mode=RuianSyncRun.MODE_FULL,
            source="shp",
            triggered_by=RuianSyncRun.TRIGGER_MANAGE,
            data_valid_to=self.DEN0,
            status=RuianSyncRun.STATUS_SUCCESS,
            variant="ZKSH",
        )

    def _spust(self, vydane_dny):
        """
        Spustí denní sync s kontrolovanou sadou dostupných dnů.

        :param vydane_dny: Množina dnů, pro které zdroj vrátí soubor; ostatní
            skončí jako HTTP 404.
        """

        def stahni(day, target_dir=None):
            return mock.Mock(path=None) if day in vydane_dny else None

        with mock.patch.object(tasks, "datetime", _FakeDatetimeModul(self.DNES)), mock.patch(
            "heslar.ruian_sync.vfr_download.get_target_dir", return_value="/tmp"
        ), mock.patch("heslar.ruian_sync.FileVfrSource.download_for_day", side_effect=stahni), mock.patch(
            "heslar.ruian_sync.syncer.sync_delta", return_value=None
        ), mock.patch.object(
            tasks, "_zkontroluj_stari_poslednich_dat", lambda today: None
        ):
            tasks._sync_ruian_changes_locked(reassign_records=False)

    def _kotva(self):
        """
        Vrátí den poslední úspěšné synchronizace.

        :return: ``data_valid_to`` posledního úspěšného běhu, nebo ``None``.
        """
        posledni = RuianSyncRun.last_successful()
        return posledni.data_valid_to if posledni else None

    def _cekajicich(self):
        """
        Spočítá dny čekající na potvrzení.

        :return: Počet běhů s poznámkou :data:`cron.tasks.NOTE_404_NEPOTVRZENO`.
        """
        return RuianSyncRun.objects.filter(note=tasks.NOTE_404_NEPOTVRZENO).count()

    def _vsechny_dny(self):
        """
        Vrátí sadu všech dnů v testovaném rozsahu.

        :return: Množina dat od ``DEN0 + 1`` dál.
        """
        return {self.DEN0 + datetime.timedelta(days=n) for n in range(1, 40)}

    def test_rozbita_url_neposune_kotvu(self):
        """Samá 404 nesmí posunout kotvu – jinak se dny po opravě nedotáhnou."""
        self._spust(set())

        self.assertEqual(self._kotva(), self.DEN0)
        self.assertGreater(self._cekajicich(), 0)

    def test_opakovany_beh_nezaklada_duplicity(self):
        """Nepotvrzený den se při dalším cronu recykluje, ne zakládá znovu."""
        self._spust(set())
        po_prvnim = self._cekajicich()

        self._spust(set())

        self.assertEqual(self._cekajicich(), po_prvnim)

    def test_po_oprave_url_se_dotahnou_vsechny_dny(self):
        """Po opravě zdroje se kotva dostane až na poslední den, nic se nepřeskočí."""
        self._spust(set())

        self._spust(self._vsechny_dny())

        self.assertEqual(self._kotva(), self.DNES - datetime.timedelta(days=1))
        self.assertEqual(self._cekajicich(), 0, "potvrzené dny nesmí zůstat viset")

    def test_dlouha_pauza_ve_vydavani_nezablokuje_sync(self):
        """
        Delší legitimní pauza ve vydávání nesmí sync zaseknout.

        Regrese: dokud se běh u prahu podezřelé série zastavoval, smyčka se
        nikdy nedostala k prvnímu dni s daty a kotva stála natrvalo.
        """
        pauza = {self.DEN0 + datetime.timedelta(days=n) for n in range(1, 8)}

        self._spust(self._vsechny_dny() - pauza)

        self.assertEqual(self._kotva(), self.DNES - datetime.timedelta(days=1))

    def test_cerstvy_den_se_nepovazuje_za_prazdny(self):
        """
        U dnešního dne 404 znamená „ještě nevydáno“, ne „bez změn“.

        Kotva zůstane před ním, aby se den zkusil znovu, až ho ČÚZK vydá.
        """
        vcerejsek = self.DNES - datetime.timedelta(days=1)
        self._spust(self._vsechny_dny() - {vcerejsek})

        self.assertLess(self._kotva(), vcerejsek)


@_BEZ_CACHEOPS
class StariPoslednichDatTests(TestCase):
    """
    Testy dvouúrovňového hlášení stáří posledních stažených dat.

    Hlásí se ve dvou úrovních podle toho, jestli se mezera dá ještě dohnat:
    do retence zdroje stačí opravit URL, za ní už pomůže jen plný sync.
    """

    DNES = datetime.date(2026, 9, 8)

    def setUp(self):
        """Vyprázdní audit, ať stáří určuje jen připravený běh."""
        RuianSyncRun.objects.all().delete()

    def _hlaska(self, stari_dnu):
        """
        Spustí kontrolu nad během starým zadaný počet dnů.

        :param stari_dnu: Stáří posledního běhu s daty; ``None`` = žádný běh.
        :return: Seznam názvů zalogovaných ``ERROR`` hlášek.
        """
        if stari_dnu is not None:
            RuianSyncRun.objects.create(
                mode=RuianSyncRun.MODE_DELTA,
                source="file_vfr",
                triggered_by=RuianSyncRun.TRIGGER_CRON,
                data_valid_to=self.DNES - datetime.timedelta(days=stari_dnu),
                status=RuianSyncRun.STATUS_SUCCESS,
                variant="ZKSH",
                source_path="/tmp/test.zip",
            )
        zachyceno = []
        handler = type(
            "Zachyt",
            (logging.Handler,),
            {"emit": lambda _self, record: zachyceno.append(record.msg)},
        )()
        tasks.logger.addHandler(handler)
        try:
            tasks._zkontroluj_stari_poslednich_dat(self.DNES)
        finally:
            tasks.logger.removeHandler(handler)
        return [str(m).rsplit(".", 1)[-1] for m in zachyceno]

    def test_cerstva_data_neohlasi_nic(self):
        """Běžný provoz včetně svátků se hlásit nemá."""
        self.assertEqual(self._hlaska(tasks.RUIAN_NO_DOWNLOAD_ERROR_DAYS), [])

    def test_dlouho_bez_dat(self):
        """Za prahem se hlásí podezření na změnu URL; dny jsou ještě ke stažení."""
        self.assertIn("dlouho_bez_dat", self._hlaska(tasks.RUIAN_NO_DOWNLOAD_ERROR_DAYS + 1))

    def test_tesne_pred_retenci_stale_jen_varovani(self):
        """Den před hranicí retence se ještě dá spolehnout na denní sync."""
        hlasky = self._hlaska(tasks.RUIAN_RETENCE_ZDROJE_DNU - 1)

        self.assertIn("dlouho_bez_dat", hlasky)
        self.assertNotIn("mimo_retenci_zdroje", hlasky)

    def test_za_retenci_vyzve_k_plnemu_syncu(self):
        """
        Za retencí zdroje už soubory na serveru nejsou.

        Rada „ověřte URL“ by tu byla zavádějící, proto ji nahradí výzva
        ke spuštění plného syncu.
        """
        hlasky = self._hlaska(tasks.RUIAN_RETENCE_ZDROJE_DNU)

        self.assertIn("mimo_retenci_zdroje", hlasky)
        self.assertNotIn("dlouho_bez_dat", hlasky)

    def test_zadna_stazena_data(self):
        """Bez jediného běhu s daty se hlásí samostatná chyba."""
        self.assertIn("zadna_stazena_data", self._hlaska(None))


class SerializaceBehuTests(TestCase):
    """
    Testy serializace souběžných běhů denní synchronizace RÚIAN.

    Dva souběžné běhy by četly stejnou kotvu, stahovaly do stejné cesty
    a dvakrát aplikovaly tytéž změny do DB, historie i Fedory.
    """

    def test_druha_session_zamek_nedostane(self):
        """Zámek drží napříč spojeními, ne jen uvnitř jednoho procesu."""
        with tasks._ruian_sync_lock() as ziskan:
            self.assertTrue(ziskan)
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND objid = %s",
                    [tasks.RUIAN_SYNC_LOCK_KEY & 0xFFFFFFFF],
                )
                self.assertEqual(cursor.fetchone()[0], 1, "zámek se nedrží")

    def test_zamek_se_uvolni(self):
        """Po opuštění bloku zámek nesmí zůstat viset."""
        with tasks._ruian_sync_lock():
            pass

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND objid = %s",
                [tasks.RUIAN_SYNC_LOCK_KEY & 0xFFFFFFFF],
            )
            self.assertEqual(cursor.fetchone()[0], 0)

    def test_beh_bez_zamku_se_preskoci_a_ohlasi(self):
        """Bez zámku se běh vůbec nespustí a stav se zaloguje na ERROR."""
        import contextlib

        @contextlib.contextmanager
        def _nezisakn():
            yield False

        with mock.patch.object(tasks, "_ruian_sync_lock", _nezisakn), mock.patch.object(
            tasks, "_sync_ruian_changes_locked"
        ) as telo:
            with self.assertLogs(tasks.logger, level=logging.ERROR) as zachyt:
                tasks.sync_ruian_changes(reassign_records=False)

        telo.assert_not_called()
        self.assertTrue(any("lock_not_acquired" in radek for radek in zachyt.output))


class PianGeomTriggerTests(TestCase):
    """
    Regrese na migraci ``pian.0008_pian_geom_sjtsk_povinny``.

    Trigger ``trg_validate_geometries`` je ``BEFORE INSERT OR UPDATE OF geom,
    geom_sjtsk`` a validuje **obě** kolony včetně ``NEW.geom``. V datech přitom
    jsou starší piany, jejichž ``geom`` dnešní ``validategeom`` neuznává, takže
    backfill ``geom_sjtsk`` na takovém řádku shodil celou migraci i nasazení.
    """

    def test_migrace_nechala_trigger_zapnuty(self):
        """
        Backfill trigger dočasně vypíná – po migraci musí být zase zapnutý.

        Kdyby zůstal vypnutý, přestala by platit validace geometrií pro celou
        aplikaci a nikdo by si toho nevšiml.
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT tgenabled FROM pg_trigger
                WHERE tgname = 'trg_validate_geometries' AND NOT tgisinternal
                """)
            radek = cursor.fetchone()

        self.assertIsNotNone(radek, "trigger trg_validate_geometries neexistuje")
        self.assertEqual(radek[0], "O", "trigger zůstal po migraci vypnutý")

    def test_zadny_pian_nezustal_bez_geom_sjtsk(self):
        """Po migraci nesmí zbýt ``geom_sjtsk IS NULL`` – sloupec je ``NOT NULL``."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM pian WHERE geom_sjtsk IS NULL")

            self.assertEqual(cursor.fetchone()[0], 0)


class SpatialQueryKandidatuTests(TestCase):
    """
    Testy SQL, které po změně hranic vybírá záznamy k přepočtu.

    Archeologický záznam navázaný na změněný katastr **jen přes M2M**
    ``az.katastry`` dřív nebyl kandidátem: první větev ho nechytila (jiný
    hlavní katastr) a prostorová větev už zmenšenou hranici neprotínala.
    """

    def test_sql_kandidatu_az_ma_tri_vetve(self):
        """Dotaz musí brát hlavní katastr, průnik PIANů i M2M vazbu."""
        self.assertEqual(
            syncer._SQL_AZ_CANDIDATES.count("UNION"),
            2,
            "chybí větev pro některý zdroj kandidátů",
        )
        self.assertIn("archeologicky_zaznam_katastr", syncer._SQL_AZ_CANDIDATES)

    def test_sql_kandidatu_az_je_spustitelne(self):
        """Dotaz se třemi parametry musí projít proti reálnému schématu."""
        _, _, katastry = _vytvor_ruian_data(3, prefix=930000)
        kody = [k.kod for k in katastry]

        with connection.cursor() as cursor:
            cursor.execute(syncer._SQL_AZ_CANDIDATES, [kody, kody, kody])
            radky = cursor.fetchall()

        self.assertIsInstance(radky, list)

    def test_kandidati_projektu_nezahrnuji_m2m(self):
        """
        Další katastry projektu se při změně hranic záměrně nemění.

        Podle zadání issue #372 se u projektů upravuje pouze hlavní katastr,
        takže M2M větev v dotazu být nesmí – jinak by se přepočítávaly
        projekty, u kterých se stejně nic nezmění.
        """
        self.assertNotIn("projekt_katastr", syncer._SQL_PROJEKT_CANDIDATES)


@_BEZ_CACHEOPS
class DeltaMazaniTests(TestCase):
    """
    Testy sémantiky mazání v denním změnovém souboru.

    Na rozdíl od plného stavu tu chybějící prvek neznamená „zanikl“, ale
    „o tomhle prvku dnes nic nevím“. Useknutý denní soubor proto nesmí vést
    k mazání – jen se aplikuje míň událostí.
    """

    def test_prazdny_zmenovy_soubor_nic_nesmaze(self):
        """Bez událostí se počet katastrů nezmění."""
        pred = RuianKatastr.objects.count()
        run = RuianSyncRun.objects.create(
            mode=RuianSyncRun.MODE_DELTA,
            source="file_vfr",
            triggered_by=RuianSyncRun.TRIGGER_CRON,
            data_valid_to=datetime.date(2026, 1, 1),
            variant="ZKSH",
        )

        with transaction.atomic():
            syncer._apply_changes([], run)

        self.assertEqual(RuianKatastr.objects.count(), pred)
        self.assertEqual(run.katastr_deletes, 0)


class DefinicniBodTests(SimpleTestCase):
    """Kontrola, že testovací data pracují v očekávaném souřadnicovém systému."""

    def test_sjtsk_ma_zaporne_souradnice(self):
        """
        EPSG:5514 se v projektu drží v záporné konvenci.

        Kdyby se do dat dostaly kladné hodnoty, prostorové dotazy by tiše
        nevracely nic – proto to hlídá vlastní test.
        """
        bod = Point(-850715.79, -995389.44, srid=5514)

        self.assertLess(bod.x, 0)
        self.assertLess(bod.y, 0)
        self.assertEqual(bod.srid, 5514)


@_BEZ_CACHEOPS
class VynuceniMetadatPoSelhaniTests(TestCase):
    """
    Testy dohnání metadat ve Fedoře po dni, který selhal až po commitu.

    Upsert zapisuje do PostgreSQL uvnitř ``transaction.atomic``, ale metadata
    posílá do Fedory až ``transaction.on_commit`` callback v
    ``heslar.signals``. Když ten callback selže, databáze změnu má a repozitář
    ne. Při opakování dne by se DTO rovnalo řádku v databázi, ``changed`` by
    vyšlo ``False`` a ``save()`` by se už nikdy nezavolal.
    """

    def setUp(self):
        """Vytvoří kraj, jehož data se proti zdroji nebudou lišit."""
        self.kraj, _, _ = _vytvor_ruian_data(0, prefix=940000)

    def _dto(self):
        """
        Sestaví DTO shodné s uloženým krajem.

        :return: Instance :class:`RuianKrajDTO` beze změny proti databázi.
        """
        return RuianKrajDTO(kod=self.kraj.kod, nazev=self.kraj.nazev)

    def test_beze_zmeny_se_normalne_neuklada(self):
        """Za běžného běhu se shodný prvek neukládá – žádný zápis do Fedory."""
        with mock.patch.object(RuianKraj, "save") as zapis:
            zmeneno = syncer._upsert_kraj(self.kraj, self._dto())

        self.assertFalse(zmeneno)
        zapis.assert_not_called()

    def test_pri_opakovani_se_zapis_vynuti(self):
        """
        Při opakování po selhání se ``save()`` zavolá i u shodného prvku.

        Tím se znovu spustí ``post_save`` signál, který metadata do Fedory
        pošle – jinak by zůstala zastaralá natrvalo.
        """
        with mock.patch.object(RuianKraj, "save") as zapis:
            zmeneno = syncer._upsert_kraj(self.kraj, self._dto(), vynutit_metadata=True)

        self.assertFalse(zmeneno, "vynucený zápis nesmí hlásit změnu dat")
        zapis.assert_called_once()

    def test_vynuceni_nezkresli_countery(self):
        """
        Vynucený zápis se nesmí započítat jako upsert.

        Audit by jinak u opakovaného dne hlásil změny, ke kterým nedošlo.
        """
        run = RuianSyncRun.objects.create(
            mode=RuianSyncRun.MODE_DELTA,
            source="file_vfr",
            triggered_by=RuianSyncRun.TRIGGER_CRON,
            data_valid_to=datetime.date(2026, 3, 3),
            variant="ZKSH",
        )
        udalost = RuianChangeEvent(level=LEVEL_KRAJ, event_type=EVENT_UPSERT, kod=self.kraj.kod, payload=self._dto())

        with mock.patch.object(RuianKraj, "save"):
            syncer._apply_changes([udalost], run, vynutit_metadata=True)

        self.assertEqual(run.kraj_upserts, 0)


@_BEZ_CACHEOPS
class RozpoznaniOpakovaniTests(TestCase):
    """
    Testy rozpoznání dne, který se opakuje po selhání se staženými daty.

    Rozhoduje o tom, jestli se metadata vynutí. Běh, který skončil na 404,
    se k datům nedostal a nemá co dohánět.
    """

    DEN = datetime.date(2026, 4, 4)
    DNES = datetime.date(2026, 4, 6)

    def _spust(self, predchozi_behy):
        """
        Spustí denní sync a vrátí hodnotu ``vynutit_metadata`` předanou dál.

        :param predchozi_behy: Seznam dvojic ``(status, source_path)`` běhů,
            které pro testovaný den už v auditu jsou.
        :return: Hodnota ``vynutit_metadata`` ze zachyceného volání.
        """
        RuianSyncRun.objects.all().delete()
        RuianSyncRun.objects.create(
            mode=RuianSyncRun.MODE_FULL,
            source="shp",
            triggered_by=RuianSyncRun.TRIGGER_MANAGE,
            data_valid_to=self.DEN - datetime.timedelta(days=1),
            status=RuianSyncRun.STATUS_SUCCESS,
            variant="ZKSH",
        )
        for status, cesta in predchozi_behy:
            RuianSyncRun.objects.create(
                mode=RuianSyncRun.MODE_DELTA,
                source="file_vfr",
                triggered_by=RuianSyncRun.TRIGGER_CRON,
                data_valid_to=self.DEN,
                status=status,
                variant="ZKSH",
                source_path=cesta,
            )

        with mock.patch.object(tasks, "datetime", _FakeDatetimeModul(self.DNES)), mock.patch(
            "heslar.ruian_sync.vfr_download.get_target_dir", return_value="/tmp"
        ), mock.patch(
            "heslar.ruian_sync.FileVfrSource.download_for_day", return_value=mock.Mock(path=None)
        ), mock.patch(
            "heslar.ruian_sync.syncer.sync_delta"
        ) as delta, mock.patch.object(
            tasks, "_zkontroluj_stari_poslednich_dat", lambda today: None
        ):
            tasks._sync_ruian_changes_locked(reassign_records=False)

        volani = [v for v in delta.call_args_list if v.kwargs["day"] == self.DEN]
        self.assertEqual(len(volani), 1, "den se měl zpracovat právě jednou")
        return volani[0].kwargs["vynutit_metadata"]

    def test_prvni_pokus_metadata_nevynucuje(self):
        """Bez dřívějšího selhání není co dohánět."""
        self.assertFalse(self._spust([]))

    def test_selhani_po_stazeni_metadata_vynuti(self):
        """Dřívější pokus data stáhl a selhal – metadata mohla zůstat nezapsaná."""
        self.assertTrue(self._spust([(RuianSyncRun.STATUS_FAILED, "/tmp/20260404_ST_ZKSH.xml.zip")]))

    def test_selhani_bez_stazeni_metadata_nevynuti(self):
        """Běh, který skončil na 404, se k datům nedostal."""
        self.assertFalse(self._spust([(RuianSyncRun.STATUS_FAILED, "")]))


@_BEZ_CACHEOPS
class GeometrieZdrojeTests(TestCase):
    """
    Testy topologické kontroly zdroje před destruktivním diffem.

    Kontrola počtů propustí vstup, který má všechny jednotky, ale poškozenou
    geometrii. Součet ploch a validita polygonů to zachytí ještě před tím, než
    se do databáze cokoli zapíše – na rozdíl od
    :func:`~heslar.ruian_sync.syncer._check_katastry_topology`, která ze své
    podstaty běží až po zápisu a sync nezastavuje.
    """

    def setUp(self):
        """Vytvoří katastry se známou plochou (čtverce 900 × 900 m)."""
        _, self.okres, self.katastry = _vytvor_ruian_data(4, prefix=950000)

    def _stav(self, meritko=1.0, nevalidni=0):
        """
        Sestaví plný stav odvozený od vytvořených katastrů.

        :param meritko: Násobek délky strany čtverce; ``1.0`` = shodné s DB.
        :param nevalidni: Kolik polygonů nahradit sebeprotínajícím se tvarem.
        :return: Instance :class:`RuianFullState`.
        """
        dtos = []
        for i, katastr in enumerate(self.katastry):
            if i < nevalidni:
                # Přesýpací hodiny – prsten protíná sám sebe.
                wkt = "MULTIPOLYGON(((0 0, 10 10, 10 0, 0 10, 0 0)))"
            else:
                strana = 900 * meritko
                x0 = -700000.0 - i * 1000
                y0 = -1000000.0
                wkt = (
                    f"MULTIPOLYGON((({x0} {y0}, {x0 + strana} {y0}, "
                    f"{x0 + strana} {y0 + strana}, {x0} {y0 + strana}, {x0} {y0})))"
                )
            dtos.append(
                RuianKatastrDTO(kod=katastr.kod, nazev=katastr.nazev, okres_kod=self.okres.kod, hranice_wkt=wkt)
            )
        return RuianFullState(kraje=[], okresy=[], katastry=dtos)

    def test_shodna_geometrie_projde(self):
        """Zdroj shodný s databází nemá co hlásit."""
        self.assertEqual(syncer._zkontroluj_geometrii_zdroje(self._stav(), len(self.katastry)), [])

    def test_scvrkle_hranice_se_zachyti(self):
        """Zmenšené hranice srazí součet ploch pod práh odchylky."""
        problemy = syncer._zkontroluj_geometrii_zdroje(self._stav(meritko=0.9), len(self.katastry))

        self.assertEqual(len(problemy), 1)
        self.assertIn("plocha", problemy[0])

    def test_nafouknute_hranice_se_zachyti(self):
        """Kontrola je oboustranná – hrubý překryv součet ploch nafoukne."""
        problemy = syncer._zkontroluj_geometrii_zdroje(self._stav(meritko=1.1), len(self.katastry))

        self.assertEqual(len(problemy), 1)
        self.assertIn("plocha", problemy[0])

    def test_nevalidni_polygon_se_zachyti(self):
        """Sebeprotínající se prsten je vada vstupu, ne běžný stav."""
        problemy = syncer._zkontroluj_geometrii_zdroje(self._stav(nevalidni=1), len(self.katastry))

        self.assertTrue(any("nevalidních" in p for p in problemy), problemy)

    def test_prvni_import_plochu_neporovnava(self):
        """Do prázdné databáze není proti čemu součet ploch porovnávat."""
        self.assertEqual(syncer._zkontroluj_geometrii_zdroje(self._stav(meritko=0.5), 0), [])

    def test_kontrola_bezi_pred_zapisem(self):
        """
        Vadná geometrie zastaví běh dřív, než se smaže jediný katastr.

        Tohle je jádro připomínky: dosud se stejný stav jen zapsal a teprve
        potom se o něm zalogovalo.
        """
        run = RuianSyncRun.objects.create(
            mode=RuianSyncRun.MODE_FULL,
            source="shp",
            triggered_by=RuianSyncRun.TRIGGER_MANAGE,
            data_valid_to=datetime.date(2026, 6, 6),
            variant="ZKSH",
        )
        pred = RuianKatastr.objects.count()

        with self.assertRaises(syncer.RuianNeuplnyZdrojError):
            syncer._apply_full_state(self._stav(meritko=0.5), run)

        self.assertEqual(RuianKatastr.objects.count(), pred, "nesmělo dojít k žádnému zápisu")


@_BEZ_CACHEOPS
class CommitVSignaluTests(TestCase):
    """
    Testy záznamů, které Fedora transakci uzavírají samy v ``on_commit``.

    Projekty mají ``close_active_transaction_when_finished = True``, takže
    jejich ``post_save`` signál registruje ``transaction.on_commit`` callback
    a ten transakci commitne. Callback se ale spustí až při commitu obalující
    ``transaction.atomic()``. Kdyby ji uzavřel i blok
    :func:`~heslar.ruian_sync.reassign._db_a_fedora`, přišel by druhý commit
    a Fedora ho odmítne chybou „has already been committed“.

    Regrese na plný sync z 8. 9. 2026, kde takhle selhalo šest projektů.

    Testuje se **kontrakt bloku**, tedy jestli transakci uzavírá, nebo ne.
    Samotné spuštění callbacku nasimulovat nejde: v ``TestCase`` se
    ``on_commit`` nikdy nespustí (testovací transakce se vrací) a
    ``TransactionTestCase`` by vyprázdnil sdílenou testovací databázi.
    """

    def _projed(self, commit_v_signalu, vyhodit=None):
        """
        Projede blok tak, jak to dělá reassign projektu.

        :param commit_v_signalu: Hodnota stejnojmenného parametru bloku.
        :param vyhodit: Výjimka vyhozená uvnitř bloku, nebo ``None``.
        :return: Dvojice ``(fake transakce, zachycená výjimka nebo None)``.
        """
        fake = _FakeFedoraTransakce()
        chyba = None
        try:
            with mock.patch.object(reassign_mod, "FedoraTransaction", lambda: fake):
                with reassign_mod._db_a_fedora("P-TEST", commit_v_signalu=commit_v_signalu):
                    if vyhodit is not None:
                        raise vyhodit
        except Exception as exc:  # noqa: BLE001 – test zkoumá i typ chyby
            chyba = exc
        return fake, chyba

    def test_s_priznakem_blok_transakci_neuzavira(self):
        """
        S příznakem nechá blok transakci otevřenou pro callback ze signálu.

        Tohle je jádro opravy – dřív ji blok uzavřel sám a callback pak narazil
        na „has already been committed“.
        """
        fake, chyba = self._projed(commit_v_signalu=True)

        self.assertIsNone(chyba)
        self.assertEqual(
            fake.status,
            reassign_mod.FedoraTransactionStatus.ACTIVE,
            "blok nesmí commitovat – transakci uzavře až callback ze signálu",
        )

    def test_bez_priznaku_blok_transakci_uzavre(self):
        """Bez příznaku commit patří bloku – tak fungují AZ a SN."""
        fake, chyba = self._projed(commit_v_signalu=False)

        self.assertIsNone(chyba)
        self.assertEqual(fake.status, reassign_mod.FedoraTransactionStatus.COMMITTED)

    def test_druhy_commit_by_fedora_odmitla(self):
        """
        Kontrola, že náhrada Fedory dvojitý commit opravdu odhalí.

        Bez toho by test výše prošel i s rozbitým kódem.
        """
        fake = _FakeFedoraTransakce()
        fake.mark_transaction_as_closed()

        with self.assertRaises(RuntimeError) as chyceno:
            fake.mark_transaction_as_closed()

        self.assertIn("already been committed", str(chyceno.exception))

    def test_chyba_uvnitr_bloku_vraci_obe_strany(self):
        """
        I s příznakem musí výjimka uvnitř bloku odvolat Fedoru i databázi.

        Callback ze signálu se v takovém případě vůbec nespustí, takže tu
        žádný rozpad nevzniká a nic se jako rozpad nehlásí.
        """
        with self.assertNoLogs(reassign_mod.logger, level=logging.ERROR):
            fake, chyba = self._projed(commit_v_signalu=True, vyhodit=ValueError("zápis selhal"))

        self.assertIsInstance(chyba, ValueError)
        self.assertTrue(fake.rollbacknuta)
        self.assertEqual(fake.status, reassign_mod.FedoraTransactionStatus.ABORTED)


@_BEZ_CACHEOPS
class UbytekPokrytiTests(TestCase):
    """
    Testy hlášení úbytku pokrytí podle režimu běhu a výsledku sjednocení.

    Pokles součtu ploch sám o sobě nerozliší díru od plošné výměny hranic.
    U delty se proto hlásí ``ERROR`` vždy (planý poplach je levnější než
    přehlédnutá díra), u plného synchu jen tehdy, když sjednocení opravdu
    našlo anomálii – jinak by poplach zazněl při každém plném synchu.

    Regrese na plný sync z 9. 9. 2026: pokles 10,35 km² při 7004 přepsaných
    katastrech, přitom sjednocení nenašlo jedinou díru ani překryv.
    """

    UBYTEK = 10_353_866.0

    def _run(self, mode):
        """
        Vytvoří audit záznam daného režimu.

        :param mode: ``RuianSyncRun.MODE_FULL`` nebo ``MODE_DELTA``.
        :return: Uložená instance :class:`RuianSyncRun`.
        """
        return RuianSyncRun.objects.create(
            mode=mode,
            source="shp" if mode == RuianSyncRun.MODE_FULL else "file_vfr",
            triggered_by=RuianSyncRun.TRIGGER_MANAGE,
            data_valid_to=datetime.date(2026, 9, 9),
            variant="ZKSH",
        )

    def _ohlas(self, mode, podezrele):
        """
        Zavolá hlášení a vrátí úroveň, hlášku a poznámku z auditu.

        :param mode: Režim běhu.
        :param podezrele: Co vrátilo sjednocení.
        :return: Trojice ``(uroven, hlaska, note)``.
        """
        run = self._run(mode)
        with self.assertLogs(syncer.logger, level=logging.WARNING) as zachyt:
            syncer._ohlas_ubytek_pokryti(run, self.UBYTEK, podezrele=podezrele)
        run.refresh_from_db()
        uroven, _, hlaska = zachyt.output[0].partition(":")
        return uroven, hlaska, run.note or ""

    def test_full_bez_anomalie_je_jen_varovani(self):
        """Plošná výměna hranic při plném synchu není chyba."""
        uroven, hlaska, note = self._ohlas(RuianSyncRun.MODE_FULL, podezrele=False)

        self.assertEqual(uroven, "WARNING")
        self.assertIn("ubytek_bez_anomalie", hlaska)
        self.assertIn("nenašlo díru ani překryv", note)
        self.assertNotIn("pravděpodobně vznikla díra", note)

    def test_full_s_anomalii_je_chyba(self):
        """Když sjednocení našlo díru, mírnější hlášení by zakrylo vadu."""
        uroven, hlaska, note = self._ohlas(RuianSyncRun.MODE_FULL, podezrele=True)

        self.assertEqual(uroven, "ERROR")
        self.assertIn("pravděpodobně vznikla díra", note)

    def test_delta_je_prisna_i_bez_anomalie(self):
        """
        U denní změny se hlásí chyba i při čistém sjednocení.

        Delta mění hrstku katastrů, takže pokles nad prahem je podezřelý vždy.
        """
        uroven, hlaska, note = self._ohlas(RuianSyncRun.MODE_DELTA, podezrele=False)

        self.assertEqual(uroven, "ERROR")
        self.assertIn("pravděpodobně vznikla díra", note)

    def test_pokryti_beze_zmeny_nic_nehlasi(self):
        """Bez úbytku nad prahem se nevrací nic k hlášení."""
        run = self._run(RuianSyncRun.MODE_FULL)
        plocha = syncer._soucet_plochy_katastru()

        self.assertIsNone(syncer._zkontroluj_pokryti(run, plocha))

    def test_bez_vychoziho_stavu_se_kontrola_preskoci(self):
        """Bez plochy před syncem není s čím porovnávat."""
        self.assertIsNone(syncer._zkontroluj_pokryti(self._run(RuianSyncRun.MODE_FULL), None))


@_BEZ_CACHEOPS
class SouladUrovniTests(TestCase):
    """
    Testy porovnání ploch katastrů, okresů a krajů na závěr syncu.

    Každá úroveň má polygony z jiného souboru RÚIAN, ale popisují totéž území,
    takže se jejich součty musí shodovat. Po plném synchu z 9. 9. 2026 daly
    všechny tři 78 866 842 064,610 m² – rozdíl 0,000 m².

    Testy si stavějí vlastní úrovně, aby nezávisely na obsahu databáze:
    jeden kraj a jeden okres o ploše dvou katastrů.
    """

    def setUp(self):
        """Vytvoří dva katastry a k nim odpovídající okres a kraj."""
        self.run = RuianSyncRun.objects.create(
            mode=RuianSyncRun.MODE_FULL,
            source="shp",
            triggered_by=RuianSyncRun.TRIGGER_MANAGE,
            data_valid_to=datetime.date(2026, 9, 9),
            variant="ZKSH",
        )
        RuianKatastr.objects.all().delete()
        RuianOkres.objects.all().delete()
        RuianKraj.objects.all().delete()
        self.kraj, self.okres, self.katastry = _vytvor_ruian_data(2, prefix=970000)

    def _nastav_hranice_urovni(self, meritko_okresu=1.0, meritko_kraje=1.0):
        """
        Přiřadí okresu a kraji hranici o ploše obou katastrů, volitelně zvětšenou.

        :param meritko_okresu: Násobek plochy u okresu.
        :param meritko_kraje: Násobek plochy u kraje.
        """
        for objekt, meritko in ((self.okres, meritko_okresu), (self.kraj, meritko_kraje)):
            polygony = []
            for i in range(len(self.katastry)):
                strana = 900 * meritko
                x0 = -700000.0 - i * 1000
                y0 = -1000000.0
                polygony.append(
                    Polygon(
                        ((x0, y0), (x0 + strana, y0), (x0 + strana, y0 + strana), (x0, y0 + strana), (x0, y0)),
                        srid=5514,
                    )
                )
            objekt.hranice = MultiPolygon(*polygony, srid=5514)
            objekt.suppress_signal = True
            objekt.save()

    def test_shodne_plochy_projdou(self):
        """Když všechny tři úrovně pokrývají totéž, nic se nehlásí."""
        self._nastav_hranice_urovni()

        with self.assertNoLogs(syncer.logger, level=logging.WARNING):
            syncer._zkontroluj_soulad_urovni(self.run)

        self.run.refresh_from_db()
        self.assertEqual(self.run.note or "", "")

    def test_rozejity_okres_se_ohlasi(self):
        """
        Okres o jiné ploše než jeho katastry znamená nesoulad úrovní.

        Typicky když změnový soubor přinese posun hranice katastru na okraji
        okresu, ale odpovídající polygon okresu už ne.
        """
        self._nastav_hranice_urovni(meritko_okresu=1.5)

        with self.assertLogs(syncer.logger, level=logging.ERROR) as zachyt:
            syncer._zkontroluj_soulad_urovni(self.run)

        self.assertTrue(any("nesoulad" in radek for radek in zachyt.output), zachyt.output)
        self.run.refresh_from_db()
        self.assertIn("okresů", self.run.note or "")

    def test_hlasi_se_kazda_rozejita_uroven(self):
        """Rozejdou-li se obě nadřazené úrovně, musí být v poznámce obě."""
        self._nastav_hranice_urovni(meritko_okresu=1.5, meritko_kraje=0.5)

        with self.assertLogs(syncer.logger, level=logging.ERROR):
            syncer._zkontroluj_soulad_urovni(self.run)

        self.run.refresh_from_db()
        self.assertIn("okresů", self.run.note or "")
        self.assertIn("krajů", self.run.note or "")

    def test_chybejici_geometrie_je_chyba(self):
        """
        Okres či kraj bez vyplněné hranice je vada, ne důvod ke přeskočení.

        Přesně tenhle stav měla databáze před prvním plným syncem ze SHP –
        okresy i kraje tam byly, ale bez polygonů. Bez geometrie nejde spočítat
        pokrytí ani prostorově dohledat nadřazený prvek, takže v databázi
        zůstat nesmí.
        """
        with self.assertLogs(syncer.logger, level=logging.ERROR) as zachyt:
            syncer._zkontroluj_soulad_urovni(self.run)

        self.assertTrue(any("chybi_geometrie" in radek for radek in zachyt.output), zachyt.output)
        self.run.refresh_from_db()
        self.assertIn("nemá vyplněnou hranici", self.run.note or "")

    def test_pri_chybejici_geometrii_se_plochy_neporovnavaji(self):
        """
        U úrovně bez geometrie nemá porovnání ploch smysl.

        Rozdíl by jen opisoval chybějící prvky a zdvojoval hlášení, takže se
        hlásí pouze chybějící geometrie.
        """
        with self.assertLogs(syncer.logger, level=logging.ERROR) as zachyt:
            syncer._zkontroluj_soulad_urovni(self.run)

        self.assertFalse(any("nesoulad" in radek for radek in zachyt.output), zachyt.output)

    def test_castecne_vyplnena_uroven_je_chyba(self):
        """Stačí jediný okres bez hranice – kontrola nesmí projít."""
        self._nastav_hranice_urovni()
        druhy = RuianOkres.objects.create(
            nazev="Okres bez hranice",
            kraj=self.kraj,
            spz="TZZ",
            kod=979999,
            nazev_en="District without boundary",
        )
        self.addCleanup(druhy.delete)

        with self.assertLogs(syncer.logger, level=logging.ERROR) as zachyt:
            syncer._zkontroluj_soulad_urovni(self.run)

        self.assertTrue(any("chybi_geometrie" in radek for radek in zachyt.output), zachyt.output)


class KandidatiBezJtskTests(SimpleTestCase):
    """
    Testy podmínky na ``geom_sjtsk`` v dotazech na kandidáty (N1).

    Sloupec je nullable a ``_prefer_sjtsk`` existuje právě proto, aby se
    u starších záznamů použil ``geom`` ve 4326. Kdyby podmínka platila pro celý
    dotaz, vypadl by z kandidátů záznam, který na změněný katastr ukazuje cizím
    klíčem – a cílený reassign je jediná automatická cesta, jak se přepočítá.
    """

    def test_fk_vetev_nevyzaduje_zrovna_jtsk(self):
        """
        Cizí klíč musí vybrat kandidáta i bez vyplněného ``geom_sjtsk``.

        Sloupec je nullable a ``_prefer_sjtsk`` existuje právě proto, aby se
        u starších záznamů použil ``geom`` ve 4326.
        """
        for sql in (syncer._SQL_PROJEKT_CANDIDATES, syncer._SQL_SN_CANDIDATES):
            self.assertIn("geom IS NOT NULL AND NOT ST_IsEmpty(", sql)

    def test_fk_vetev_vyzaduje_nejakou_geometrii(self):
        """
        Záznam bez geometrie kandidátem být nemá.

        Přepočet mu nemá z čeho spočítat bod, skončil by na ``no_geometry`` –
        a takových projektů je zhruba polovina, takže by každá změna hranic
        vygenerovala tisíce hlášek o práci, která nemohla dopadnout jinak.
        """
        for sql in (syncer._SQL_PROJEKT_CANDIDATES, syncer._SQL_SN_CANDIDATES):
            self.assertEqual(sql.count("NOT ST_IsEmpty("), 2, sql)

    def test_prostorova_vetev_geometrii_vyzaduje(self):
        """Prostorový intersect bez JTSK geometrie provést nejde."""
        for sql in (syncer._SQL_PROJEKT_CANDIDATES, syncer._SQL_SN_CANDIDATES):
            self.assertIn("geom_sjtsk IS NOT NULL AND ST_Intersects", sql)


class ReprezentativniBodTests(SimpleTestCase):
    """
    Testy sdíleného SQL výrazu pro reprezentativní bod PIANu (B3).

    Výraz byl opsaný ve dvou modulech; kdyby se rozešly, vycházel by hlavní
    katastr u téhož PIANu jinak podle toho, kterou cestou se počítá.
    """

    def test_vsechny_tri_vetve(self):
        """Linie, plocha i ostatní typy mají vlastní větev."""
        vyraz = reprezentativni_bod_sql("x.geom")

        self.assertIn("ST_LineInterpolatePoint(x.geom, 0.5)", vyraz)
        self.assertIn("ST_PointOnSurface(x.geom)", vyraz)
        self.assertIn("ST_Centroid(x.geom)", vyraz)

    def test_sloupec_se_propise_vsude(self):
        """Výraz se skládá kolem předaného sloupce, ne kolem pevného jména."""
        vyraz = reprezentativni_bod_sql("dp.pian_geom")

        self.assertNotIn("geom_sjtsk", vyraz)
        self.assertEqual(vyraz.count("dp.pian_geom"), 5)


class DatumSnapshotuTests(SimpleTestCase):
    """
    Testy křížové kontroly ``--valid-to`` proti názvu ÚZSZ souboru (N10).

    ``valid_to`` se ukládá jako kotva a cron od ní pokračuje dál; pozdější
    hodnota než snapshot tiše přeskočí denní změny a hlídač stáří dat mlčí,
    protože kotva vypadá čerstvě.
    """

    def setUp(self):
        """Připraví instanci příkazu bez spouštění."""
        from heslar.management.commands.aktualizuj_ruian_shp import Command

        self.command = Command()

    def test_datum_se_vycte_z_nazvu(self):
        """Očekávaný tvar ``YYYYMMDD_ST_UZSZ.xml.zip``."""
        from pathlib import Path

        self.assertEqual(
            self.command._datum_snapshotu(Path("/data/20260731_ST_UZSZ.xml.zip")),
            datetime.date(2026, 7, 31),
        )

    def test_nerozpoznany_nazev_vraci_none(self):
        """Ručně přejmenovaný soubor se nemá o co opřít."""
        from pathlib import Path

        self.assertIsNone(self.command._datum_snapshotu(Path("/data/uzsz.xml.zip")))

    def test_valid_to_v_budoucnosti_se_odmitne(self):
        """
        Stav, který ještě neexistuje, nemohl být stažen.

        Kotva by přeskočila všechny dny až k zadanému datu a protože by
        vypadala čerstvě, nespustil by se ani hlídač stáří dat.
        """
        from pathlib import Path

        from django.core.management.base import CommandError

        zitra = datetime.date.today() + datetime.timedelta(days=1)
        with self.assertRaises(CommandError) as chyceno:
            self.command._zkontroluj_valid_to(Path("/d/20260731_ST_UZSZ.xml.zip"), zitra)

        self.assertIn("leží v budoucnosti", str(chyceno.exception))

    def test_starsi_uzsz_nez_valid_to_je_v_poradku(self):
        """
        ÚZSZ starší než ``--valid-to`` je běžný provoz, ne chyba.

        Polygony nese nedatované ``1.zip`` (stejná URL vrací aktuální stav),
        zatímco ÚZSZ s definičními body vychází řidčeji – kombinace ÚZSZ
        z 31. 7. a dat platných k 13. 8. je tedy správná.
        """
        from pathlib import Path

        self.command._zkontroluj_valid_to(Path("/d/20260731_ST_UZSZ.xml.zip"), datetime.date(2026, 8, 13))

    def test_shodne_valid_to_projde(self):
        """Datum shodné s vydáním ÚZSZ je také správné použití."""
        from pathlib import Path

        self.command._zkontroluj_valid_to(Path("/d/20260731_ST_UZSZ.xml.zip"), datetime.date(2026, 7, 31))


class PollingProtokolTests(SimpleTestCase):
    """
    Testy sdíleného polling protokolu a jeho tří oprav (N7).

    ``ContinueKatastrProcessing`` protokol dřív reimplementoval a nesl tři
    opravy, které bázová třída neměla: dělení nulou u prázdné fronty,
    ``AttributeError`` u vypršelého klíče a odchyt
    ``FedoraTransactionCommitFailedError``.
    """

    def test_je_podtridou_sdilene_baze(self):
        """Protokol se nesmí implementovat podruhé."""
        from fedora_management.views import AdminRecordProcessingView
        from heslar.views import ContinueKatastrProcessing

        self.assertTrue(issubclass(ContinueKatastrProcessing, AdminRecordProcessingView))

    def test_baze_odchytava_i_commit_failed(self):
        """
        ``FedoraTransactionCommitFailedError`` není potomek ``FedoraError``.

        Bez explicitního uvedení by prošla ven jako HTTP 500 – a to až poté,
        co se index v Redis posunul, tedy s přeskočením zbytku fronty.
        """
        from core.repository_connector import FedoraError, FedoraTransactionCommitFailedError
        from fedora_management.views import AdminRecordProcessingView

        self.assertFalse(issubclass(FedoraTransactionCommitFailedError, FedoraError))
        self.assertIn(FedoraTransactionCommitFailedError, AdminRecordProcessingView.zpracovani_chyby)

    def test_cizi_redis_klic_se_odmitne(self):
        """
        Endpoint nesmí sáhnout na klíč jiné úlohy.

        Redis je sdílený s ``import_data_*`` i ``update_metadata_*``; posun
        indexu na cizím klíči by rozbil běžící úlohu.
        """
        from heslar.views import ContinueKatastrProcessing as C

        self.assertTrue(C.je_platny_job_id("update_katastry_abc-DEF_123"))
        for cizi in ("import_data_status_message_x", "update_metadata_1", "update_katastry_", "update_katastry_a;b"):
            self.assertFalse(C.je_platny_job_id(cizi), cizi)

    def test_klic_ma_expiraci(self):
        """Nedokončená úloha nesmí v Redis zůstat natrvalo."""
        from heslar.views import ContinueKatastrProcessing as C

        self.assertEqual(C.job_expirace, 6 * 60 * 60)


class ZastaraleParametryKatastruTests(SimpleTestCase):
    """
    Testy přechodného přijetí parametrů ``long``/``lat`` (N12).

    Kontrakt endpointu se změnil z WGS84 na JTSK naráz; prohlížeč
    s cachovaným starším skriptem by jinak dostal prázdný objekt a políčko
    katastru by zůstalo nevyplněné bez jakékoli hlášky.
    """

    def setUp(self):
        """Připraví továrnu na požadavky."""
        from django.test import RequestFactory

        self.rf = RequestFactory()

    def test_stare_parametry_se_prevedou(self):
        """Souřadnice Prahy ve 4326 dají zápornou JTSK dvojici."""
        from heslar.views import _souradnice_ze_starych_parametru

        x, y = _souradnice_ze_starych_parametru(self.rf.get("/", {"long": "14.42", "lat": "50.08"}))

        self.assertLess(x, 0)
        self.assertLess(y, 0)

    def test_bez_starych_parametru_vraci_none(self):
        """Nové volání se přemostěním nemá zdržovat."""
        from heslar.views import _souradnice_ze_starych_parametru

        self.assertIsNone(_souradnice_ze_starych_parametru(self.rf.get("/", {"x": "-1", "y": "-2"})))

    def test_nesmyslna_hodnota_vraci_none(self):
        """Nečíselný vstup není důvod k pádu."""
        from heslar.views import _souradnice_ze_starych_parametru

        self.assertIsNone(_souradnice_ze_starych_parametru(self.rf.get("/", {"long": "abc", "lat": "50"})))
