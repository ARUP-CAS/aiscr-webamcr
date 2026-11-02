"""
Souhrn varování z logu do auditu běhu synchronizace RÚIAN.

Řada varování vzniká hluboko v parseru, stahování nebo přepočtu navázaných
záznamů, kde záznam běhu (:class:`heslar.models.RuianSyncRun`) není
k dispozici. Taková varování dřív končila jen v logu a v administraci nebyla
vidět. :class:`SberVarovani` je během běhu zachytává přímo z loggerů
a na konci zapíše do ``RuianSyncRun.warnings`` **souhrn** – jeden řádek za
druh události s počtem výskytů a několika příklady. Řádek za každý výskyt by
tabulku zaplavil (např. ``no_geometry`` jde při plném přepočtu do tisíců).

Detail jednotlivých výskytů zůstává v logu; klíč události v souhrnu slouží
k jeho dohledání v Kibaně.
"""

import logging
import threading
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

#: Loggery modulů, ze kterých se varování sbírají. Handler se věší přímo na
#: ně, ne na společného předka – nezávisí tak na nastavení ``propagate``.
LOGGERY = (
    "heslar.ruian_sync.syncer",
    "heslar.ruian_sync.reassign",
    "heslar.ruian_sync.vfr_parser",
    "heslar.ruian_sync.shp_importer",
    "heslar.ruian_sync.vfr_download",
    "cron.tasks",
)

#: Sledované události a jejich popis do auditu. Klíč je text logové zprávy
#: (``event``), nebo jeho začátek, pokud končí tečkou či podtržítkem – tak se jedním
#: pravidlem pokryje rodina událostí (např. chyby Fedory pro různé typy
#: záznamů). Události, které syncer do ``warnings`` zapisuje sám přes
#: ``_append_run_warning``, tu záměrně nejsou, aby se nezdvojovaly.
UDALOSTI: Dict[str, str] = OrderedDict(
    [
        # Změny dat RÚIAN
        (
            "heslar.ruian_sync.syncer._log_hranice_change_if_significant.significant",
            "Výrazná změna hranice prvku (plocha o víc než 5 % nebo úbytek vrcholů o víc než 50 %)",
        ),
        (
            "heslar.ruian_sync.syncer._log_hranice_change_if_significant.bod_outside",
            "Definiční bod leží mimo novou hranici prvku",
        ),
        ("heslar.ruian_sync.syncer._upsert_okres.precislovani", "Okres změnil kód (přečíslování)"),
        ("heslar.ruian_sync.syncer._dohledej_okres_prostorove.ok", "Okres katastru dohledán až podle polohy"),
        ("heslar.ruian_sync.syncer._dohledej_okres_prostorove.nenalezen", "Okres katastru se nepodařilo dohledat"),
        ("heslar.ruian_sync.syncer._geos_or_none.invalid_wkt", "Neplatná geometrie ve zdroji"),
        ("heslar.ruian_sync.syncer._apply_changes.unknown_level", "Neznámá úroveň prvku ve změnovém souboru"),
        # Parser vstupu
        ("heslar.ruian_sync.vfr_parser._linearize_arcstring.invalid_point_count", "Oblouk s neplatným počtem bodů"),
        (
            "heslar.ruian_sync.vfr_parser._gml_multisurface_to_wkt.nepodporovany_prvek",
            "Nepodporovaný geometrický prvek ve VFR",
        ),
        (
            "heslar.ruian_sync.vfr_parser._gml_multisurface_to_wkt.vnorena_cast_jako_dira",
            "Vnořená část plochy převedena na díru",
        ),
        (
            "heslar.ruian_sync.shp_importer._resolve_shp_layer.stale_unpacked",
            "Rozbalená vrstva SHP byla starší než archiv, stará kopie smazána",
        ),
        (
            "heslar.ruian_sync.shp_importer._centroid_wkt.fallback_used",
            "ÚZSZ neposkytlo definiční bod, použit centroid polygonu",
        ),
        ("heslar.ruian_sync.shp_importer._centroid_wkt.error", "Nepodařilo se spočítat centroid"),
        ("heslar.ruian_sync.shp_importer._centroid_wkt.empty_centroid", "Centroid polygonu vyšel prázdný"),
        # Přepočet navázaných záznamů
        (
            "heslar.ruian_sync.syncer._reassign_records_in_changed_katastry.",
            "Přepočet katastru záznamu selhal",
        ),
        ("heslar.ruian_sync.reassign._db_a_fedora.metadata_nezapsana", "Metadata záznamu se nezapsala do Fedory"),
        ("heslar.ruian_sync.reassign._db_a_fedora.rozpad_db_fedora", "Databáze a Fedora se u záznamu rozešly"),
        ("heslar.ruian_sync.reassign._close_or_rollback.rollback_selhal", "Rollback transakce Fedory selhal"),
        ("heslar.ruian_sync.reassign.reassign_az.fallback_bez_pianu", "Katastr AZ určen bez PIANu"),
        ("heslar.ruian_sync.reassign.reassign_projekt.no_geometry", "Projekt bez geometrie – katastr nelze přepočítat"),
        ("heslar.ruian_sync.reassign.reassign_az.no_geometry", "AZ bez geometrie – katastr nelze přepočítat"),
        ("heslar.ruian_sync.reassign.reassign_sn.no_geometry", "SN bez geometrie – katastr nelze přepočítat"),
        (
            "heslar.ruian_sync.reassign.reassign_neident_akce.no_geometry",
            "Neidentifikovaná akce bez geometrie – katastr nelze přepočítat",
        ),
        ("heslar.ruian_sync.reassign._prefer_sjtsk.transform_failed", "Převod souřadnic do S-JTSK selhal"),
        (
            "heslar.ruian_sync.syncer._delete_katastr.reassign_",
            "Přesun záznamů ze zrušeného katastru: chyba Fedory",
        ),
        ("heslar.ruian_sync.syncer._log_katastr_rename.", "Propagace přejmenování katastru: chyba"),
        ("heslar.ruian_sync.syncer._smaz_fedora_kontejner_okresu.error", "Kontejner okresu ve Fedoře nešel smazat"),
        # Stahování
        (
            "heslar.ruian_sync.vfr_download.download_change_file.atom_failed",
            "Stažení přes ATOM feed selhalo, zkoušela se náhradní URL",
        ),
        ("heslar.ruian_sync.vfr_download._je_duveryhodny_odkaz.odmitnuto", "Odmítnut nedůvěryhodný odkaz z ATOM feedu"),
        ("cron.tasks.sync_ruian_changes.source_remove_failed", "Stažený soubor nešel smazat"),
    ]
)

#: Kolik příkladů (kódů nebo identů) se u události nejvýš vypíše.
MAX_PRIKLADU = 5

#: Atributy záznamu logu, ze kterých se berou příklady – v pořadí priority.
_POLE_PRIKLADU = ("ident_cely", "kod", "file", "href", "day")


def _klic_udalosti(zprava: str) -> Optional[str]:
    """
    Najde v :data:`UDALOSTI` pravidlo odpovídající zprávě logu.

    Přesná shoda má přednost; jinak rozhoduje nejdelší prefix (pravidlo
    končící tečkou nebo podtržítkem).

    :param zprava: Text logové zprávy.
    :return: Klíč z :data:`UDALOSTI`, nebo ``None`` když se událost nesleduje.
    """
    if zprava in UDALOSTI:
        return zprava
    prefixy = [k for k in UDALOSTI if k.endswith((".", "_")) and zprava.startswith(k)]
    return max(prefixy, key=len) if prefixy else None


class _Handler(logging.Handler):
    """Počítá sledované události z vlákna, které běh spustilo."""

    def __init__(self, sber: "SberVarovani"):
        """
        Připraví handler pro daný sběr.

        :param sber: Sběr, do kterého se události zapisují.
        """
        super().__init__(level=logging.WARNING)
        self.sber = sber

    def emit(self, record: logging.LogRecord) -> None:
        """
        Započítá záznam, pokud je sledovaný a pochází z vlákna běhu.

        Filtr na vlákno brání tomu, aby se do auditu přimíchala varování
        z jiných požadavků obsluhovaných týmž procesem.

        :param record: Záznam logu.
        """
        if record.thread != self.sber.vlakno:
            return
        klic = _klic_udalosti(str(record.msg))
        if klic is None:
            return
        zaznam = self.sber.vysledky.setdefault(klic, [0, [], set()])
        zaznam[0] += 1
        priklady, udalosti = zaznam[1], zaznam[2]
        udalosti.add(str(record.msg))
        if len(priklady) < MAX_PRIKLADU:
            for pole in _POLE_PRIKLADU:
                hodnota = getattr(record, pole, None)
                if hodnota not in (None, "") and str(hodnota) not in priklady:
                    priklady.append(str(hodnota))
                    break


class SberVarovani:
    """
    Sbírá varování z logu během jednoho běhu a na konci je shrne do auditu.

    Použití: ``sber = SberVarovani(run).start()`` před během a
    ``sber.zapis()`` v ``finally`` – souhrn se zapíše i tehdy, když běh
    selže, protože právě pak je nejcennější.
    """

    def __init__(self, run):
        """
        Připraví sběr pro daný běh.

        :param run: Audit záznam :class:`heslar.models.RuianSyncRun`.
        """
        self.run = run
        self.vlakno: Optional[int] = None
        self.vysledky: Dict[str, List] = OrderedDict()
        self._handler = _Handler(self)

    def start(self) -> "SberVarovani":
        """
        Připojí handler k loggerům :data:`LOGGERY`.

        :return: Sám sebe, pro zápis ``SberVarovani(run).start()``.
        """
        self.vlakno = threading.get_ident()
        for jmeno in LOGGERY:
            logging.getLogger(jmeno).addHandler(self._handler)
        return self

    def souhrn(self) -> List[str]:
        """
        Sestaví řádky souhrnu v pořadí :data:`UDALOSTI`.

        :return: Řádky ve tvaru ``popis: N× (příklady) [událost]``.
        """
        radky = []
        for klic, popis in UDALOSTI.items():
            if klic not in self.vysledky:
                continue
            pocet, priklady, udalosti = self.vysledky[klic]
            text = f"{popis}: {pocet}×"
            if priklady:
                text += " (např. " + ", ".join(priklady) + ")"
            text += " [" + ", ".join(sorted(udalosti)) + "]"
            radky.append(text)
        return radky

    def zapis(self) -> Tuple[str, ...]:
        """
        Odpojí handler a připíše souhrn do ``RuianSyncRun.warnings``.

        Řádek, který už ve ``warnings`` je (opakovaný pokus o tentýž den se
        stejným výsledkem), se nepřidává znovu.

        Volá se z ``finally``, proto **nikdy nevyhazuje**: selhání zápisu
        (typicky ztracené spojení s databází u už selhaného běhu) by jinak
        nahradilo skutečnou výjimku běhu, případně přeskočilo uložení
        úspěšného stavu. Souhrn se pak jen zaloguje.

        :return: Nově připsané řádky; prázdné, když se zápis nepodařil.
        """
        for jmeno in LOGGERY:
            logging.getLogger(jmeno).removeHandler(self._handler)

        nove: Tuple[str, ...] = ()
        try:
            from heslar.ruian_sync.syncer import _append_run_warning

            stavajici = set((self.run.warnings or "").splitlines())
            nove = tuple(r for r in self.souhrn() if r not in stavajici)
            for radek in nove:
                _append_run_warning(self.run, radek)
        except Exception as err:  # noqa: BLE001 – zápis souhrnu nesmí shodit běh
            logger.error(
                "heslar.ruian_sync.souhrn_varovani.zapis_selhal",
                extra={"run_id": getattr(self.run, "pk", None), "error": str(err)[:500], "souhrn": self.souhrn()},
            )
            return ()
        return nove
