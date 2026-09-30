"""
Posun, deformace a generování náhodných poloh pro anonymizaci databáze.

Doplněk k :mod:`core.management.commands.utils.anonymizace` zaměřený na
geometrii. Veškerá práce probíhá v EPSG:5514 (S-JTSK), kde jsou jednotky metry
– po issue #372 jsou v tomto systému jak RÚIAN vrstvy, tak klady mapových listů
i ``Pian.geom_sjtsk``, takže odpadá jakýkoli převod souřadnic. Hodnota
``Pian.geom`` v EPSG:4326 se z výsledku dopočítává až na konci funkcí
``core.coordTransform.transform_geom_to_wgs84``.

Anonymizace polohy stojí na třech krocích:

* **posun** na náhodnou polohu uvnitř povolené oblasti,
* **kontrola minimálního posunu**, aby nová poloha nepadla těsně vedle původní,
* **deformace tvaru**, protože obrys plochy nebo průběh linie kopíruje reálnou
  stavbu či parcelu a je identifikující i po přesunu jinam.
"""

import contextlib
import logging
import math

from django.contrib.gis.geos import GEOSGeometry, LinearRing, LineString, MultiPolygon, Point, Polygon

logger = logging.getLogger(__name__)

#: Podíl charakteristického rozměru geometrie, o který se smí posunout vrchol
#: při deformaci. Drží deformaci úměrnou velikosti tvaru, aby se malá sonda
#: nerozpadla a velká plocha jen mírně zvlnila.
POMER_DEFORMACE = 0.05

#: Dolní mez posunu vrcholu v metrech. Bez ní by u velmi malých geometrií
#: vyšla deformace prakticky nulová a tvar by zůstal rozpoznatelný.
MIN_DEFORMACE_M = 0.5

#: Počet pokusů o zmenšení deformace, než se tvar nechá jen posunutý.
POKUSY_DEFORMACE = 3

#: Typy geometrie, které databázový trigger u PIANu připouští.
POVOLENE_TYPY = ("Point", "LineString", "Polygon", "MultiPolygon")

#: Typy, u kterých databáze kontroluje minimální délku segmentu.
#:
#: Funkce ``validategeom`` volá ``validateLine`` jen ve větvích pro
#: ``ST_LineString`` a ``ST_Polygon``; ``ST_MultiPolygon`` projde bez kontroly
#: segmentů. Replika to musí dodržet, jinak odmítá hranice katastrů, které
#: databáze bez problémů přijme.
TYPY_S_KONTROLOU_SEGMENTU = ("LineString", "Polygon")

#: Obálky, uvnitř kterých musí geometrie PIANu ležet, podle SRID.
#: Odpovídají mezím ve funkci ``validategeom`` v databázi.
OBALKA_PODLE_SRID = {
    5514: (-905000.0, -1230000.0, -400000.0, -930000.0),
    4326: (5.0, 40.0, 25.0, 60.0),
}

#: Nejkratší přípustná délka segmentu v metrech (EPSG:5514).
#:
#: Přesná mez z databázové funkce ``validateLine``, kterou volá trigger
#: ``validate_geom_fields_trigger``; kratší segment znamená chybu
#: ``segmentsTooShort``. Hodnota musí odpovídat databázi, ne být přísnější –
#: přísnější mez by zbytečně odmítala geometrie, které by zápisem prošly.
MIN_DELKA_SEGMENTU_M = 0.11

#: Nejkratší přípustná délka segmentu ve stupních (EPSG:4326).
#:
#: Týž trigger kontroluje i kopii geometrie ve WGS-84 a má tam vlastní mez.
#: Kontrolovat obojí je nutné: mez ve stupních umí porušit i geometrie, která
#: v S-JTSK projde, a hlavně ji porušují některé záznamy už ve zdrojových
#: datech – trigger totiž validuje celou geometrii, ne jen to, co jsme změnili.
MIN_DELKA_SEGMENTU_STUPNE = 1e-6

#: Mez použitá při zkoušení deformovaného tvaru, s rezervou nad databázovou.
#:
#: Deformace posouvá vrcholy náhodně, takže tvar těsně nad databázovou mezí by
#: se mohl dostat pod ni. Rezerva platí jen pro kandidáty na deformaci; hotová
#: geometrie se posuzuje přesnou databázovou mezí, jinak bychom odmítali
#: geometrie, které se do databáze bez problémů zapisují.
MIN_DELKA_SEGMENTU_DEFORMACE_M = 0.15


@contextlib.contextmanager
def tise_geos():
    """
    Dočasně ztlumí hlášky knihovny GEOS o neplatné geometrii.

    Kontrola kandidáta na deformovaný tvar se dělá tak, že se geometrie zkusí
    postavit a zeptat se jí na platnost. GEOS přitom na každou neplatnou
    variantu zaloguje ``Self-intersection``, takže úspěšný běh vypíše stovky
    varování o tvarech, které jsme právě zahodili – a skutečná varování v tom
    zaniknou. Hlášky se proto na dobu zkoušení ztlumí; chování GEOS ani
    výsledek kontroly to nemění.

    :return: Generátor bez hodnoty; po opuštění bloku se úroveň logování vrátí.
    """
    gis_logger = logging.getLogger("django.contrib.gis")
    puvodni_uroven = gis_logger.level
    gis_logger.setLevel(logging.ERROR)
    try:
        yield
    finally:
        gis_logger.setLevel(puvodni_uroven)


def reprezentativni_bod(geom):
    """
    Vrátí reprezentativní bod geometrie podle jejího typu.

    Pythonový protějšek SQL výrazu ``core.utils.reprezentativni_bod_sql``;
    obojí musí volit týž bod, jinak by hlavní katastr vycházel podle toho,
    kterou cestou se počítá. U linie je to střed, u plochy bod ležící vždy
    uvnitř (centroid může u konkávního tvaru padnout mimo), jinak centroid.

    :param geom: Geometrie ``GEOSGeometry`` v libovolném souřadnicovém systému.
    :return: Bod ``Point`` se shodným SRID jako vstup.
    """
    if geom.geom_type == "LineString":
        return geom.interpolate_normalized(0.5)
    if geom.geom_type in ("Polygon", "MultiPolygon"):
        return geom.point_on_surface
    return geom.centroid


def spocitej_posun(stary_bod, novy_bod):
    """
    Spočítá vektor posunu mezi dvěma body.

    :param stary_bod: Výchozí bod ``Point`` v EPSG:5514.
    :param novy_bod: Cílový bod ``Point`` v EPSG:5514.
    :return: Dvojice ``(dx, dy)`` v metrech.
    """
    return novy_bod.x - stary_bod.x, novy_bod.y - stary_bod.y


def vzdalenost(prvni_bod, druhy_bod):
    """
    Vrátí euklidovskou vzdálenost dvou bodů v metrech.

    Souřadnice jsou v EPSG:5514, takže stačí rovinný výpočet a není třeba
    volat ``ST_Distance`` nad geografií.

    :param prvni_bod: První bod ``Point``.
    :param druhy_bod: Druhý bod ``Point``.
    :return: Vzdálenost v metrech jako ``float``.
    """
    return math.hypot(druhy_bod.x - prvni_bod.x, druhy_bod.y - prvni_bod.y)


def splnuje_minimalni_posun(stary_bod, novy_bod, min_posun_m):
    """
    Ověří, že nová poloha je od původní dostatečně daleko.

    Bez této kontroly může náhodný bod padnout těsně vedle původní polohy
    a záznam by nebyl anonymizovaný.

    :param stary_bod: Původní poloha ``Point`` v EPSG:5514.
    :param novy_bod: Navržená nová poloha ``Point`` v EPSG:5514.
    :param min_posun_m: Minimální požadovaná vzdálenost v metrech;
        nula nebo záporná hodnota kontrolu vypíná.
    :return: ``True``, pokud je vzdálenost alespoň ``min_posun_m``.
    """
    if min_posun_m <= 0:
        return True
    return vzdalenost(stary_bod, novy_bod) >= min_posun_m


def posun_geometrii(geom, dx, dy):
    """
    Posune celou geometrii o zadaný vektor.

    Zachovává typ geometrie i počet vrcholů, mění jen souřadnice.

    :param geom: Geometrie ``GEOSGeometry`` v EPSG:5514.
    :param dx: Posun ve směru osy X v metrech.
    :param dy: Posun ve směru osy Y v metrech.
    :return: Nová geometrie ``GEOSGeometry`` se shodným SRID.
    """
    return _mapuj_vrcholy(geom, lambda x, y: (x + dx, y + dy))


def posun_bodu_3d(bod, dx, dy):
    """
    Posune trojrozměrný bod v rovině a ponechá jeho výšku.

    Používá se pro ``VyskovyBod.geom``, kde souřadnice ``z`` je niveleta, tedy
    výška, nikoli poloha – posouvat ji by změnilo naměřený údaj. Znaménková
    konvence projektu (``Point(x=-abs(northing), y=-abs(easting))``) zůstává
    zachována, protože posun je řádově menší než samotné souřadnice.

    :param bod: Bod ``Point`` v EPSG:5514, očekává se s rozměrem ``z``.
    :param dx: Posun ve směru osy X v metrech.
    :param dy: Posun ve směru osy Y v metrech.
    :return: Nový bod ``Point`` se zachovanou souřadnicí ``z``.
    """
    if bod.hasz:
        return Point(bod.x + dx, bod.y + dy, bod.z, srid=bod.srid)
    return Point(bod.x + dx, bod.y + dy, srid=bod.srid)


def charakteristicky_rozmer(geom):
    """
    Vrátí charakteristický rozměr geometrie v metrech.

    Slouží jako měřítko pro velikost deformace: u plochy odmocnina z obsahu,
    u linie její délka. Bod žádný rozměr nemá.

    :param geom: Geometrie ``GEOSGeometry`` v EPSG:5514.
    :return: Rozměr v metrech; nula pro bodové geometrie.
    """
    if geom.geom_type in ("Polygon", "MultiPolygon"):
        return math.sqrt(abs(geom.area))
    if geom.geom_type in ("LineString", "MultiLineString", "LinearRing"):
        return geom.length
    return 0.0


def velikost_deformace(geom, max_posun_m):
    """
    Spočítá, o kolik metrů se smí posunout jednotlivý vrchol.

    Výsledek je úměrný velikosti geometrie, ale vždy v mezích
    :data:`MIN_DEFORMACE_M` až ``max_posun_m``.

    :param geom: Geometrie ``GEOSGeometry`` v EPSG:5514.
    :param max_posun_m: Horní mez posunu vrcholu v metrech.
    :return: Povolený posun vrcholu v metrech; nula znamená bez deformace.
    """
    if max_posun_m <= 0:
        return 0.0
    rozmer = charakteristicky_rozmer(geom)
    if rozmer <= 0:
        return 0.0
    return min(max(POMER_DEFORMACE * rozmer, MIN_DEFORMACE_M), max_posun_m)


def deformuj_geometrii(geom, max_posun_m, generator):
    """
    Mírně zdeformuje tvar geometrie náhodným posunem jednotlivých vrcholů.

    Samotný posun na jinou polohu k anonymizaci nestačí – obrys výzkumné plochy
    nebo průběh liniového PIANu kopíruje reálnou stavbu, parcelu či trasu, takže
    je rozpoznatelný i jinde. Deformace zachovává typ geometrie, počet vrcholů
    i uzavřenost prstenců, aby zůstala v souladu s ``Pian.typ``.

    Pokud deformovaný tvar není platný (například se prstenec protne sám se
    sebou), posun se opakovaně půlí. Po vyčerpání pokusů se vrací vstupní
    geometrie beze změny – ``ST_MakeValid`` se záměrně nepoužívá, protože umí
    změnit typ geometrie i počet vrcholů.

    :param geom: Geometrie ``GEOSGeometry`` v EPSG:5514.
    :param max_posun_m: Horní mez posunu jednoho vrcholu v metrech;
        nula deformaci vypíná.
    :param generator: Instance ``random.Random`` pro reprodukovatelnost.
    :return: Dvojice ``(geometrie, deformovano)``, kde ``deformovano`` říká,
        zda se tvar opravdu změnil.
    """
    posun = velikost_deformace(geom, max_posun_m)
    if posun <= 0:
        return geom, False

    for _pokus in range(POKUSY_DEFORMACE):
        kandidat = _mapuj_vrcholy(geom, _vrcholovy_sum(posun, generator), uzavrena_kopie=True)
        if _je_pouzitelna(kandidat):
            return kandidat, True
        posun /= 2

    logger.debug(
        "core.management.commands.utils.anonymizace_geometrie.deformace_neplatna",
        extra={"geom_type": geom.geom_type, "max_posun_m": max_posun_m},
    )
    return geom, False


def _vrcholovy_sum(posun, generator):
    """
    Vytvoří funkci posouvající vrchol o náhodný vektor dané maximální délky.

    Směr je rovnoměrný na kružnici, délka rovnoměrná v intervalu od nuly
    po ``posun``.

    :param posun: Maximální délka posunu vrcholu v metrech.
    :param generator: Instance ``random.Random``.
    :return: Funkce přijímající ``(x, y)`` a vracející posunutou dvojici.
    """

    def posun_vrcholu(x, y):
        """
        Posune jeden vrchol o náhodný vektor.

        :param x: Souřadnice X v metrech.
        :param y: Souřadnice Y v metrech.
        :return: Dvojice posunutých souřadnic.
        """
        uhel = generator.uniform(0, 2 * math.pi)
        delka = generator.uniform(0, posun)
        return x + delka * math.cos(uhel), y + delka * math.sin(uhel)

    return posun_vrcholu


def _je_pouzitelna(geom):
    """
    Ověří, že deformovaná geometrie je platná a neprotíná se sama se sebou.

    :param geom: Geometrie ``GEOSGeometry`` ke kontrole.
    :return: ``True``, pokud je geometrie použitelná k uložení.
    """
    try:
        if not ma_dost_dlouhe_segmenty(geom, MIN_DELKA_SEGMENTU_DEFORMACE_M):
            return False
        with tise_geos():
            if geom.geom_type in ("Polygon", "MultiPolygon"):
                return geom.valid
            return geom.simple and geom.valid
    except Exception as err:
        logger.warning(
            "core.management.commands.utils.anonymizace_geometrie.kontrola_selhala",
            extra={"error": str(err)},
        )
        return False


def ma_dost_dlouhe_segmenty(geom, min_delka=None):
    """
    Ověří, že žádný segment geometrie není kratší než povolená mez.

    Kontrola existuje kvůli databázovému triggeru ``validate_geom_fields_trigger``,
    který takový zápis odmítne s chybou ``segmentsTooShort``. Mez se liší podle
    souřadnicového systému, protože trigger porovnává vzdálenosti v jednotkách
    dané soustavy.

    :param geom: Geometrie ``GEOSGeometry``.
    :param min_delka: Mez v jednotkách geometrie; bez zadání se odvodí ze SRID.
    :return: ``True``, pokud jsou všechny segmenty dost dlouhé.
    """
    if min_delka is None:
        min_delka = MIN_DELKA_SEGMENTU_STUPNE if geom.srid == 4326 else MIN_DELKA_SEGMENTU_M
    for rada in _rady_souradnic(geom):
        for prvni, druhy in zip(rada, rada[1:]):
            if math.dist(prvni, druhy) < min_delka:
                return False
    return True


def splnuje_pravidla_databaze(geom):
    """
    Ověří, že geometrie projde databázovým triggerem u PIANu.

    Replikuje pravidla funkce ``validategeom`` volané z
    ``validate_geom_fields_trigger``: povolený typ, dvourozměrnost, poloha
    uvnitř obálky, platnost, jednoduchost, neprázdnost a minimální délka
    segmentu. Kontrola se dělá v Pythonu, aby se kvůli každému kandidátovi
    nechodilo do databáze a aby se nevalidní zápis nestal chybou celé dávky.

    Trigger validuje **celou** geometrii, ne jen změněnou část, takže neprojde
    ani záznam, který porušoval pravidla už ve zdrojových datech. Takový PIAN
    se nechá beze změny.

    :param geom: Geometrie ``GEOSGeometry`` v EPSG:5514 nebo EPSG:4326.
    :return: ``True``, pokud by zápis prošel.
    """
    try:
        if geom.geom_type not in POVOLENE_TYPY:
            return False
        if geom.hasz:
            return False
        with tise_geos():
            if geom.empty or not geom.valid or not geom.simple:
                return False
        obalka = OBALKA_PODLE_SRID.get(geom.srid)
        if obalka is not None:
            min_x, min_y, max_x, max_y = obalka
            geom_min_x, geom_min_y, geom_max_x, geom_max_y = geom.extent
            if geom_min_x < min_x or geom_min_y < min_y or geom_max_x > max_x or geom_max_y > max_y:
                return False
        # Databáze měří délku segmentů jen u linie a polygonu; multipolygon
        # (typicky hranice katastru) touto kontrolou neprochází.
        if geom.geom_type not in TYPY_S_KONTROLOU_SEGMENTU:
            return True
        return ma_dost_dlouhe_segmenty(geom)
    except Exception as err:
        logger.warning(
            "core.management.commands.utils.anonymizace_geometrie.kontrola_pravidel_selhala",
            extra={"error": str(err)},
        )
        return False


def _rady_souradnic(geom):
    """
    Rozloží geometrii na jednotlivé řady souřadnic.

    :param geom: Geometrie ``GEOSGeometry``.
    :return: Generátor seznamů dvojic ``(x, y)``.
    """
    if geom.geom_type == "Point":
        return
    if geom.geom_type in ("LineString", "LinearRing"):
        yield [(x, y) for x, y, *_zbytek in geom.coords]
        return
    if geom.geom_type == "Polygon":
        for prstenec in geom.coords:
            yield [(x, y) for x, y, *_zbytek in prstenec]
        return
    for prvek in geom:
        yield from _rady_souradnic(prvek)


def _mapuj_vrcholy(geom, funkce, uzavrena_kopie=False):
    """
    Použije transformační funkci na všechny vrcholy geometrie.

    Rekurzivně prochází složené typy a znovu je sestaví v původní struktuře,
    takže typ geometrie ani počet vrcholů se nemění.

    :param geom: Geometrie ``GEOSGeometry`` v EPSG:5514.
    :param funkce: Funkce ``(x, y)`` vracející novou dvojici souřadnic.
    :param uzavrena_kopie: Pokud ``True``, dostane u uzavřených prstenců
        poslední vrchol tentýž posun jako první, aby prstenec zůstal uzavřený.
        Při prostém posunu celé geometrie to není třeba, protože se vrcholy
        posouvají shodně.
    :return: Nová geometrie ``GEOSGeometry`` se shodným SRID.
    """
    srid = geom.srid

    if geom.geom_type == "Point":
        x, y = funkce(geom.x, geom.y)
        if geom.hasz:
            return Point(x, y, geom.z, srid=srid)
        return Point(x, y, srid=srid)

    if geom.geom_type in ("LineString", "LinearRing"):
        souradnice = _mapuj_radu(geom.coords, funkce, uzavrena_kopie)
        trida = LinearRing if geom.geom_type == "LinearRing" else LineString
        return trida(souradnice, srid=srid)

    if geom.geom_type == "Polygon":
        prstence = [LinearRing(_mapuj_radu(prstenec, funkce, uzavrena_kopie)) for prstenec in geom.coords]
        return Polygon(*prstence, srid=srid)

    if geom.geom_type == "MultiPolygon":
        polygony = []
        for polygon in geom:
            prstence = [LinearRing(_mapuj_radu(prstenec, funkce, uzavrena_kopie)) for prstenec in polygon.coords]
            polygony.append(Polygon(*prstence))
        return MultiPolygon(*polygony, srid=srid)

    # Zbývající typy (MultiLineString, MultiPoint, GeometryCollection) se
    # v PIANech nevyskytují; zpracují se přes WKT, aby funkce nikdy nevrátila
    # geometrii jiného typu, než dostala.
    return _mapuj_pres_prvky(geom, funkce, uzavrena_kopie)


def _mapuj_pres_prvky(geom, funkce, uzavrena_kopie):
    """
    Zpracuje složenou geometrii po jednotlivých prvcích.

    :param geom: Složená geometrie ``GEOSGeometry``.
    :param funkce: Funkce ``(x, y)`` vracející novou dvojici souřadnic.
    :param uzavrena_kopie: Předává se dál do :func:`_mapuj_vrcholy`.
    :return: Nová geometrie téhož typu.
    """
    prvky = [_mapuj_vrcholy(prvek, funkce, uzavrena_kopie) for prvek in geom]
    wkt_prvku = ", ".join(prvek.wkt for prvek in prvky)
    return GEOSGeometry(f"GEOMETRYCOLLECTION({wkt_prvku})", srid=geom.srid)


def _mapuj_radu(souradnice, funkce, uzavrena_kopie):
    """
    Použije transformační funkci na řadu souřadnic.

    Funkce mění jen rovinné souřadnice. Další složky vrcholu – typicky ``z``
    u trojrozměrné geometrie – se přenesou beze změny. Trigger sice dnes 3D
    geometrii PIANu odmítá, ve starších datech se ale vyskytnout může, a jediná
    taková linie nebo plocha by jinak shodila celou sekci ``geometrie``.

    :param souradnice: Posloupnost vrcholů ``(x, y)`` nebo ``(x, y, z)``.
    :param funkce: Funkce ``(x, y)`` vracející novou dvojici souřadnic.
    :param uzavrena_kopie: Pokud ``True`` a řada je uzavřená, poslední vrchol
        převezme hodnotu prvního.
    :return: Seznam nových vrcholů se stejným počtem složek jako vstup.
    """
    body = list(souradnice)
    je_uzavrena = len(body) > 2 and body[0] == body[-1]

    def mapuj(vrchol):
        """
        Převede jeden vrchol a zachová jeho další složky.

        :param vrchol: N-tice ``(x, y, *dalsi)``.
        :return: N-tice s převedenými ``x``, ``y`` a nezměněným zbytkem.
        """
        x, y, *dalsi = vrchol
        return (*funkce(x, y), *dalsi)

    if uzavrena_kopie and je_uzavrena:
        nove = [mapuj(vrchol) for vrchol in body[:-1]]
        nove.append(nove[0])
        return nove

    return [mapuj(vrchol) for vrchol in body]


class GeneratorPoloh:
    """
    Zdroj náhodných poloh uvnitř povolené oblasti.

    Body generuje PostGIS funkcí ``ST_GeneratePoints``, která je rozmístí
    rovnoměrně uvnitř zadaného polygonu. Aby se kvůli každému záznamu nechodilo
    do databáze, generují se po dávkách a drží se v paměti; do Pythonu se přitom
    nikdy nenačítají samotné hranice okresů ani katastrů, jen hotové body.

    Povolená oblast se liší podle typu záznamu:

    * **PIAN** – průnik původního okresu a původního listu ZM50. Omezení na
      list je tu proto, že ``Pian.ident_cely`` obsahuje číslo listu ZM50;
      kdyby se PIAN přesunul jinam, přestal by ident odpovídat sloupci ``zm50``.
    * **ostatní záznamy** – celý původní okres.

    Veškeré souřadnice jsou v EPSG:5514.
    """

    def __init__(self, velikost_davky=500):
        """
        Inicializuje generátor s prázdnou vyrovnávací pamětí.

        :param velikost_davky: Počet bodů načtených jedním dotazem do PostGIS.
        """
        self.velikost_davky = velikost_davky
        self._zasoba = {}
        self._prazdne_oblasti = set()

    def nova_poloha_pro_pian(self, okres_id, zm50_gid, stary_bod, min_posun_m, pokusy=5):
        """
        Vrátí náhodný bod uvnitř průniku okresu a listu ZM50.

        :param okres_id: Primární klíč původního okresu.
        :param zm50_gid: Identifikátor ``Kladyzm.gid`` původního listu ZM50.
        :param stary_bod: Původní poloha ``Point`` pro kontrolu minimálního posunu.
        :param min_posun_m: Minimální vzdálenost nové polohy od původní v metrech.
        :param pokusy: Kolik kandidátů se smí zahodit kvůli malé vzdálenosti.
        :return: Bod ``Point`` v EPSG:5514, nebo ``None``, pokud se nepodařilo
            najít vyhovujícího kandidáta.
        """
        return self._vyber_bod(("pian", okres_id, zm50_gid), stary_bod, min_posun_m, pokusy)

    def nova_poloha_v_okrese(self, okres_id, stary_bod, min_posun_m, pokusy=5):
        """
        Vrátí náhodný bod uvnitř okresu.

        :param okres_id: Primární klíč původního okresu.
        :param stary_bod: Původní poloha ``Point`` pro kontrolu minimálního posunu.
        :param min_posun_m: Minimální vzdálenost nové polohy od původní v metrech.
        :param pokusy: Kolik kandidátů se smí zahodit kvůli malé vzdálenosti.
        :return: Bod ``Point`` v EPSG:5514, nebo ``None``.
        """
        return self._vyber_bod(("okres", okres_id), stary_bod, min_posun_m, pokusy)

    def _vyber_bod(self, klic, stary_bod, min_posun_m, pokusy):
        """
        Vybere ze zásoby prvního kandidáta splňujícího minimální posun.

        :param klic: Klíč oblasti ve vyrovnávací paměti.
        :param stary_bod: Původní poloha ``Point``.
        :param min_posun_m: Minimální vzdálenost v metrech.
        :param pokusy: Maximální počet zahozených kandidátů.
        :return: Bod ``Point``, nebo ``None`` při vyčerpání pokusů.
        """
        for _pokus in range(pokusy):
            kandidat = self._dalsi_bod(klic)
            if kandidat is None:
                return None
            if stary_bod is None or splnuje_minimalni_posun(stary_bod, kandidat, min_posun_m):
                return kandidat
        logger.warning(
            "core.management.commands.utils.anonymizace_geometrie.min_posun_nesplnen",
            extra={"klic": str(klic), "min_posun_m": min_posun_m},
        )
        return None

    def _dalsi_bod(self, klic):
        """
        Vydá další bod ze zásoby a v případě potřeby ji doplní z databáze.

        :param klic: Klíč oblasti ve vyrovnávací paměti.
        :return: Bod ``Point``, nebo ``None``, pokud je oblast prázdná.
        """
        if klic in self._prazdne_oblasti:
            return None
        zasoba = self._zasoba.get(klic)
        if not zasoba:
            zasoba = self._nacti_davku(klic)
            if not zasoba:
                # Prázdný průnik si pamatujeme, ať se kvůli dalším záznamům
                # téhož okresu a listu nechodí do databáze znovu.
                self._prazdne_oblasti.add(klic)
                return None
            self._zasoba[klic] = zasoba
        return zasoba.pop()

    def _nacti_davku(self, klic):
        """
        Načte z PostGIS novou dávku náhodných bodů.

        :param klic: Klíč oblasti ve vyrovnávací paměti.
        :return: Seznam bodů ``Point``; prázdný seznam pro prázdnou oblast.
        """
        from django.db import connection

        if klic[0] == "pian":
            _druh, okres_id, zm50_gid = klic
            dotaz = (
                "SELECT ST_AsEWKT((ST_Dump(ST_GeneratePoints("
                "ST_Intersection(o.hranice, z.the_geom), %s))).geom) "
                "FROM ruian_okres o, kladyzm z WHERE o.id = %s AND z.gid = %s"
            )
            parametry = [self.velikost_davky, okres_id, zm50_gid]
        else:
            _druh, okres_id = klic
            dotaz = (
                "SELECT ST_AsEWKT((ST_Dump(ST_GeneratePoints(o.hranice, %s))).geom) "
                "FROM ruian_okres o WHERE o.id = %s"
            )
            parametry = [self.velikost_davky, okres_id]

        with connection.cursor() as kurzor:
            kurzor.execute(dotaz, parametry)
            return [GEOSGeometry(radek[0]) for radek in kurzor.fetchall() if radek[0] is not None]
