import logging
import random

from core.constants import PRISTUPNOST_MIN_RAZENI, ROLE_ADMIN_ID
from core.coordTransform import transform_geom_to_wgs84
from core.management.commands.utils import anonymizace
from core.management.commands.utils.anonymizace_geometrie import (
    GeneratorPoloh,
    deformuj_geometrii,
    posun_bodu_3d,
    posun_geometrii,
    reprezentativni_bod,
    splnuje_minimalni_posun,
    splnuje_pravidla_databaze,
    spocitej_posun,
)
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models import Case, F, Q, TextField, Value, When
from django.db.models.functions import Cast, Concat

logger = logging.getLogger(__name__)

#: Sekce, na které je anonymizace rozdělená. Pořadí je závazné: ``geometrie``
#: musí běžet až po zápisu PIANů, protože z nich počítá katastry.
SEKCE = ("uzivatele", "oznamovatele", "logy", "texty", "geometrie", "pid")

#: Souřadnicové systémy, které sekce ``geometrie`` očekává. Po issue #372 leží
#: RÚIAN vrstvy i klady mapových listů v S-JTSK, takže prostorové dotazy běží
#: bez převodu; jediné pole ve WGS-84 je ``pian.geom``, které se dopočítává.
OCEKAVANE_SRID = {
    ("ruian_katastr", "hranice"): 5514,
    ("ruian_katastr", "definicni_bod"): 5514,
    ("ruian_okres", "hranice"): 5514,
    ("kladyzm", "the_geom"): 5514,
    ("pian", "geom_sjtsk"): 5514,
    ("pian", "geom"): 4326,
}

#: Zkratka přesnosti PIANu, jehož geometrií je celá hranice katastru.
PRESNOST_KATASTR = "4"

#: Kolikrát se zkusí najít nová poloha, než se záznam nechá beze změny.
POKUSY_POLOHY = 5

#: Podíl hlavní deformace použitý na rozptýlení jednotlivých výškových bodů.
POMER_JITTERU_VB = 0.1

#: Trigger, který při zápisu PIANu validuje geometrii (issue #3289).
TRIGGER_VALIDACE_PIANU = "trg_validate_geometries"

#: Kolik identifikátorů se u jednoho důvodu vypíše, než se seznam zkrátí.
#: Úplný seznam jde vždy do logu, výpis na konzoli má zůstat čitelný.
MAX_VYPSANYCH_IDENTU = 50


class Command(BaseCommand):
    """
    Django management příkaz pro anonymizaci databáze na testovacím serveru.

    Spouští se nad obnovenou kopií produkční databáze **před** generováním
    metadat, tedy v pořadí: obnova zálohy → ``anonymizace_dat`` →
    ``generate_metadata`` (případně jeho rychlejší varianta
    ``generate_metadata_fast``, kterou používá migrace dat podle #3967).
    Metadata se pak vytvoří už z anonymizovaných dat.

    **Příkaz je nevratný a patří výhradně na testovací server.** Chrání ho dvě
    pojistky, které platí současně: ``settings.TEST_ENV`` musí být zapnuté
    a musí být předán přepínač ``--potvrzuji-testovaci-server``.

    Co příkaz mění:

    - osobní údaje uživatelů mimo administrátorské a umělé účty, včetně hesel,
    - údaje oznamovatelů,
    - IP adresy přihlášení a adresy příjemců notifikací,
    - chráněná textová pole podle ``xml_generator/definitions/amcr.xsd``,
    - polohy záznamů s přístupností vyšší než A,
    - uložené hodnoty ``doi`` a ``igsn`` na prefix cílové instance.

    Parametry:
    - --potvrzuji-testovaci-server: Povinné potvrzení, že běh míří na testovací server.
    - --ocekavana-databaze: Název databáze, se kterým se musí shodovat cílová databáze.
    - --dry-run: Pouze vypíše počty dotčených záznamů, nic neuloží.
    - --jen: Čárkou oddělený seznam sekcí, které se mají provést.
    - --vynechat: Čárkou oddělený seznam sekcí, které se mají přeskočit.
    - --batch-size: Velikost dávky při zápisu geometrií a identifikátorů.
    - --deformace-m: Horní mez posunu jednoho vrcholu při deformaci tvaru.
    - --min-posun-m: Minimální vzdálenost nové polohy od původní.
    - --seed: Zrno generátoru náhody pro reprodukovatelný běh.

    Poznámka:
    - Záznamy se zapisují přes ``QuerySet.update()`` a ``bulk_update`` se
      zapnutým ``suppress_signal``, takže nevznikají zápisy do Fedory ani
      záznamy v historii. Metadata se stejně generují znovu až po anonymizaci.
    - ``Pian.ident_cely`` a ``Adb.ident_cely`` zůstávají původní, protože je
      na ně navázaný obsah Fedory. Nová poloha PIANu se proto hledá jen uvnitř
      původního listu ZM50 a ``Adb.sm5`` se nemění. Po anonymizaci tedy
      ``check_pian_properties`` hlásí nesoulad kladu SM5 s geometrií.
    - Uvnitř původního okresu a listu ZM50 leží zaručeně jen reprezentativní
      bod přesunutého PIANu (střed linie, bod uvnitř plochy). Velká plocha
      nebo dlouhá linie poblíž hranice okresu ji po posunu a deformaci může
      částečně přesahovat; katastry záznamu se přesto odvozují od polohy
      nové geometrie, takže s ní zůstávají v souladu.
    - Katastry chráněných záznamů, které nejde odvodit z přesunutých PIANů
      (záznam bez PIANu, se všemi PIANy ponechanými na místě nebo bez průniku
      s katastrem), a další katastry chráněných projektů se nahradí náhodnými
      katastry téhož okresu. U částečně přesunutého záznamu se katastry počítají
      jen z přesunutých PIANů.
    - Běžní uživatelé se po anonymizaci nepřihlásí heslem; použitelné zůstávají
      administrátorské účty a přihlášení přes CAS.
    - Staré verze metadat ve Fedoře a OCFL příkaz nečistí, to řeší migrace dat.
    - PIANy, jejichž geometrie porušuje pravidla databáze už v produkci, se
      zapíšou s dočasně vypnutým triggerem ``trg_validate_geometries`` – jen
      v transakci jejich dávky, takže při pádu se vypnutí vrátí. Vadu, kterou
      by vyrobila až anonymizace, příkaz nezapíše nikdy. Bez oprávnění k vypnutí
      triggeru se takové PIANy přeskočí.
    - Na konci běhu se zneplatní cacheops cache, protože dávkový zápis se
      potlačenými signály ji sám neaktualizuje. Redis snapshoty seznamů příkaz
      nepřegenerovává, jen na ně upozorní.

    Příklady použití::

    python manage.py anonymizace_dat --potvrzuji-testovaci-server --dry-run
    python manage.py anonymizace_dat --potvrzuji-testovaci-server
    python manage.py anonymizace_dat --potvrzuji-testovaci-server --jen uzivatele,logy
    python manage.py anonymizace_dat --potvrzuji-testovaci-server --jen geometrie --min-posun-m 250
    """

    help = "Anonymizuje data v databázi testovacího serveru po migraci z produkce."

    def __init__(self, *args, **kwargs):
        """
        Inicializuje příkaz a připraví počitadla sekcí.

        :param args: Poziční argumenty předané rodičovské třídě.
        :param kwargs: Pojmenované argumenty předané rodičovské třídě.
        """
        super().__init__(*args, **kwargs)
        self.statistika = {}
        self.duvody_preskoceni = {}
        self.identy_preskocenych = {}
        self.lze_vypnout_trigger = False
        self.piany_s_vadou_zdroje = set()
        self.generator_nahody = random.Random()
        self.generator_poloh = None
        self.katastry_okresu = {}
        self.az_s_prepoctenymi_katastry = set()

    def _zaklad(self, model):
        """
        Vrátí výchozí množinu záznamů modelu, nad kterou sekce pracují.

        V ostrém běhu jsou to všechny záznamy. Metoda existuje kvůli testům,
        které ji přepíšou a omezí běh na několik vybraných záznamů – jinak by
        test nad kopií produkční databáze přepisoval statisíce řádků.

        :param model: Třída modelu.
        :return: ``QuerySet`` se všemi záznamy modelu.
        """
        return model.objects.all()

    def add_arguments(self, parser):
        """
        Registruje argumenty příkazu.

        :param parser: Argumentový parser pro přidání nových parametrů příkazu.
        """
        parser.add_argument(
            "--potvrzuji-testovaci-server",
            action="store_true",
            default=False,
            help="Povinné potvrzení, že cílová databáze je testovací a data se smí nevratně přepsat.",
        )
        parser.add_argument(
            "--ocekavana-databaze",
            type=str,
            default=None,
            help="Název databáze, se kterým se musí shodovat cílová databáze.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Pouze vypíše počty dotčených záznamů, nic neuloží.",
        )
        parser.add_argument(
            "--jen",
            type=str,
            default=None,
            help="Čárkou oddělený seznam sekcí, které se mají provést.",
        )
        parser.add_argument(
            "--vynechat",
            type=str,
            default=None,
            help="Čárkou oddělený seznam sekcí, které se mají přeskočit.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Velikost dávky při zápisu geometrií a identifikátorů.",
        )
        parser.add_argument(
            "--deformace-m",
            type=float,
            default=10.0,
            help="Horní mez posunu jednoho vrcholu při deformaci tvaru; nula deformaci vypne.",
        )
        parser.add_argument(
            "--min-posun-m",
            type=float,
            default=100.0,
            help="Minimální vzdálenost nové polohy od původní v metrech; nula kontrolu vypne.",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Zrno generátoru náhody pro reprodukovatelný běh.",
        )

    def handle(self, *args, **options):
        """
        Provede vybrané sekce anonymizace nad cílovou databází.

        :param args: Poziční argumenty příkazu (nepoužívá se).
        :param options: Pojmenované argumenty z příkazového řádku.
        :raises CommandError: Pokud neprojdou pojistky nebo je zadána neznámá sekce.
        """
        self._overr_pojistky(options)
        sekce = self._vyber_sekce(options)

        if options["seed"] is not None:
            self.generator_nahody = random.Random(options["seed"])

        logger.debug(
            "core.management.commands.anonymizace_dat.start",
            extra={"sekce": ",".join(sekce), "dry_run": options["dry_run"]},
        )
        self._vypis_banner(sekce, options)

        for nazev in sekce:
            self.statistika[nazev] = {"zpracovano": 0, "zmeneno": 0, "preskoceno": 0, "chyb": 0}
            self.stdout.write("")
            self.stdout.write(f"--- {nazev} ---")
            getattr(self, f"_sekce_{nazev}")(options)

        self._invaliduj_cache(options)
        self._vypis_shrnuti(options)
        logger.debug("core.management.commands.anonymizace_dat.end", extra={"statistika": str(self.statistika)})

    def _overr_pojistky(self, options):
        """
        Ověří, že běh míří na testovací server.

        Obě podmínky musí platit současně – ``TEST_ENV`` má výchozí hodnotu
        ``True``, takže sama o sobě před omylem nechrání.

        :param options: Pojmenované argumenty z příkazového řádku.
        :raises CommandError: Pokud kterákoli pojistka neprojde.
        """
        databaze = settings.DATABASES["default"]
        popis = f"databáze {databaze.get('NAME')} na {databaze.get('HOST')}"

        if not settings.TEST_ENV:
            raise CommandError(f"TEST_ENV není zapnuté, takže {popis} vypadá jako produkční. Anonymizace se neprovede.")
        if not options["potvrzuji_testovaci_server"]:
            raise CommandError(
                f"Nevratně přepíše {popis}, DOI prefix {settings.DOI_PREFIX or '(prázdný)'}, "
                f"IGSN prefix {settings.IGSN_PREFIX or '(prázdný)'}. "
                "Spusť znovu s přepínačem --potvrzuji-testovaci-server."
            )
        ocekavana = options["ocekavana_databaze"]
        if ocekavana is not None and ocekavana != databaze.get("NAME"):
            raise CommandError(f"Očekávaná databáze {ocekavana}, ale připojená je {databaze.get('NAME')}.")

    def _vyber_sekce(self, options):
        """
        Sestaví seznam sekcí k provedení podle přepínačů.

        :param options: Pojmenované argumenty z příkazového řádku.
        :return: N-tice názvů sekcí v závazném pořadí.
        :raises CommandError: Pokud je zadán neznámý název sekce.
        """
        vybrane = set(SEKCE)
        if options["jen"]:
            vybrane = {nazev.strip() for nazev in options["jen"].split(",") if nazev.strip()}
        if options["vynechat"]:
            vybrane -= {nazev.strip() for nazev in options["vynechat"].split(",") if nazev.strip()}

        nezname = vybrane - set(SEKCE)
        if nezname:
            raise CommandError(f"Neznámé sekce: {', '.join(sorted(nezname))}. Známé jsou: {', '.join(SEKCE)}.")
        return tuple(nazev for nazev in SEKCE if nazev in vybrane)

    def _vypis_banner(self, sekce, options):
        """
        Vypíše úvodní přehled toho, co se bude měnit.

        :param sekce: N-tice názvů sekcí k provedení.
        :param options: Pojmenované argumenty z příkazového řádku.
        """
        databaze = settings.DATABASES["default"]
        rezim = "DRY-RUN (nic se neuloží)" if options["dry_run"] else "OSTRÝ BĚH (nevratné)"
        self.stdout.write("=" * 60)
        self.stdout.write(f"Databáze:    {databaze.get('NAME')} na {databaze.get('HOST')}")
        self.stdout.write(f"DOI prefix:  {settings.DOI_PREFIX or '(prázdný)'}")
        self.stdout.write(f"IGSN prefix: {settings.IGSN_PREFIX or '(prázdný)'}")
        self.stdout.write(f"Sekce:       {', '.join(sekce)}")
        self.stdout.write(f"Režim:       {rezim}")
        self.stdout.write("=" * 60)

    def _vypis_shrnuti(self, options):
        """
        Vypíše závěrečné počty za jednotlivé sekce.

        :param options: Pojmenované argumenty z příkazového řádku.
        """
        self.stdout.write("")
        self.stdout.write("=" * 60)
        for nazev, pocty in self.statistika.items():
            self.stdout.write(
                f"{nazev:14s} zpracováno {pocty['zpracovano']:8d}  změněno {pocty['zmeneno']:8d}  "
                f"přeskočeno {pocty['preskoceno']:6d}  chyb {pocty['chyb']:4d}"
            )
        self.stdout.write("=" * 60)

        chyb = sum(pocty["chyb"] for pocty in self.statistika.values())
        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry-run: žádné změny nebyly uloženy."))
        elif chyb:
            self.stdout.write(self.style.WARNING(f"Dokončeno s {chyb} chybami."))
        else:
            self.stdout.write(self.style.SUCCESS("Anonymizace dokončena."))

    def _invaliduj_cache(self, options):
        """
        Zneplatní cacheops cache a upozorní na Redis snapshoty.

        Sekce zapisují přes ``QuerySet.update()`` a ``bulk_update`` s potlačenými
        signály, takže cacheops o změně nemá jak vědět: automaticky invaliduje
        jen zápisy přes ``save()``, případně explicitní ``invalidated_update()``.
        Bez tohoto kroku by vyhledávání ještě deset minut vracelo z cache
        neanonymizovaná data – tedy přesně to, čemu má příkaz zabránit.

        Používá se ``invalidate_all`` a ne ``invalidate_model`` po jednotlivých
        modelech: anonymizace přepíše podstatnou část databáze, takže zahodit
        celou cache je jednodušší i spolehlivější než udržovat seznam modelů.
        Zásah je přitom ohraničený – ``invalidate_all`` volá ``flushdb`` nad
        databází z ``CACHEOPS_REDIS``, která patří výhradně cacheops, takže se
        nedotkne Redis snapshotů ani Django cache. Stejně to dělá příprava
        selenium testů po obnově databáze.

        :param options: Pojmenované argumenty z příkazového řádku.
        """
        from cacheops import invalidate_all

        if options["dry_run"]:
            return

        invalidate_all()
        logger.debug("core.management.commands.anonymizace_dat.cache.invalidovano")
        self.stdout.write("")
        self.stdout.write("Zneplatněna cacheops cache.")
        self.stdout.write(
            self.style.WARNING(
                "Redis snapshoty seznamů příkaz nemění. "
                "Přegeneruj Redis snapshoty pomocí update_all_redis_snapshots(rewrite_existing=True)."
            )
        )

    def _zapocti(self, sekce, zpracovano=0, zmeneno=0, preskoceno=0, chyb=0):
        """
        Přičte hodnoty do počitadel sekce.

        :param sekce: Název sekce.
        :param zpracovano: Počet prošlých záznamů.
        :param zmeneno: Počet změněných záznamů.
        :param preskoceno: Počet záznamů ponechaných beze změny.
        :param chyb: Počet chyb.
        """
        pocty = self.statistika[sekce]
        pocty["zpracovano"] += zpracovano
        pocty["zmeneno"] += zmeneno
        pocty["preskoceno"] += preskoceno
        pocty["chyb"] += chyb

    def _zapocti_duvod(self, duvod, ident_cely=None):
        """
        Přičte jeden výskyt důvodu, proč záznam zůstal beze změny.

        Důvody se sbírají a vypisují souhrnně. Varování u každého záznamu zvlášť
        by u tisíců PIANů zahltilo výstup natolik, že by se v něm skutečný
        problém ztratil. Identifikátory se přitom uchovají, aby šlo dohledat,
        kterých konkrétních záznamů se to týká.

        :param duvod: Strojový název důvodu.
        :param ident_cely: Identifikátor dotčeného záznamu; bez něj se jen počítá.
        """
        self.duvody_preskoceni[duvod] = self.duvody_preskoceni.get(duvod, 0) + 1
        if ident_cely:
            self.identy_preskocenych.setdefault(duvod, []).append(ident_cely)

    def _vypis_duvody(self):
        """Vypíše souhrn důvodů, proč některé záznamy zůstaly beze změny."""
        popisy = {
            "bez_nove_polohy": "nepodařilo se najít novou polohu ve stejném okresu a listu ZM50",
            "bez_nahradniho_katastru": "nenašel se náhradní katastr ve stejném okresu a listu ZM50",
            "neplatna_geometrie": "výsledná geometrie by neprošla kontrolou v databázi",
            "zapsano_s_vadou_zdroje": (
                "přesunuto i přes vadu zdrojové geometrie, trigger validace byl při zápisu vypnut"
            ),
            "zdrojova_geometrie_neplatna": (
                "pravidla databáze porušuje už zdrojová geometrie (krátký segment nebo protínající se tvar)"
            ),
            "bez_deformace": "tvar se nepodařilo zdeformovat, PIAN je pouze posunutý",
            "bez_nahodneho_katastru": "okres nemá jiný katastr, hlavní katastr záznamu zůstal původní",
        }
        if not self.duvody_preskoceni:
            return
        self.stdout.write("")
        for duvod, pocet in sorted(self.duvody_preskoceni.items(), key=lambda polozka: -polozka[1]):
            self.stdout.write(f"  {pocet}× {popisy.get(duvod, duvod)}")
            self._vypis_identy(duvod)
        logger.info(
            "core.management.commands.anonymizace_dat.geometrie.duvody",
            extra={"duvody": str(self.duvody_preskoceni), "identy": str(self.identy_preskocenych)},
        )

    def _vypis_identy(self, duvod):
        """
        Vypíše identifikátory záznamů spadajících pod zadaný důvod.

        Dlouhý seznam se na konzoli zkrátí, celý jde do logu – u desítek tisíc
        PIANů by jinak výpis přerostl vše ostatní.

        :param duvod: Strojový název důvodu.
        """
        identy = self.identy_preskocenych.get(duvod)
        if not identy:
            return
        ukazka = identy[:MAX_VYPSANYCH_IDENTU]
        self.stdout.write("    " + ", ".join(ukazka))
        if len(identy) > len(ukazka):
            self.stdout.write(f"    a dalších {len(identy) - len(ukazka)}")

    def _sekce_uzivatele(self, options):
        """
        Anonymizuje osobní údaje uživatelů mimo vyloučené účty.

        Vyloučené jsou účty ve skupině administrátorů a umělé účty s řetězcem
        ``Anonym`` v příjmení. Zápis jde jedním ``UPDATE``, protože ``User.save()``
        normalizuje e-mail a zakládá vazbu do historie.

        :param options: Pojmenované argumenty z příkazového řádku.
        :raises CommandError: Pokud by zástupné adresy kolidovaly s vyloučeným účtem.
        """
        from uzivatel.models import User

        vsichni = self._zaklad(User)
        k_anonymizaci = vsichni.exclude(groups__id=ROLE_ADMIN_ID).exclude(
            last_name__icontains=anonymizace.VYJIMKA_PRIJMENI
        )
        pocet = k_anonymizaci.count()
        self._zapocti("uzivatele", zpracovano=pocet)
        self.stdout.write(f"Uživatelů k anonymizaci: {pocet} z {vsichni.count()}")

        kolize = vsichni.filter(email__regex=r"^uzivatel_[0-9]+@" + anonymizace.ANONYM_DOMENA.replace(".", r"\.") + "$")
        kolize = kolize.exclude(pk__in=k_anonymizaci.values("pk"))
        if kolize.exists():
            identy = ", ".join(kolize.values_list("ident_cely", flat=True)[:10])
            raise CommandError(f"Vyloučené účty už mají zástupnou adresu, hrozí kolize unikátního e-mailu: {identy}")

        if options["dry_run"]:
            return

        pks = list(k_anonymizaci.values_list("pk", flat=True))
        zmeneno = User.objects.filter(pk__in=pks).update(
            first_name=Concat(Value("Jméno_"), Cast("id", TextField()), output_field=TextField()),
            last_name=Concat(Value("Příjmení_"), Cast("id", TextField()), output_field=TextField()),
            email=Concat(
                Value("uzivatel_"),
                Cast("id", TextField()),
                Value(f"@{anonymizace.ANONYM_DOMENA}"),
                output_field=TextField(),
            ),
            telefon=Case(
                When(Q(telefon__isnull=True) | Q(telefon=""), then=F("telefon")),
                default=Value(anonymizace.ANONYM_TELEFON),
                output_field=TextField(),
            ),
            password=Value(anonymizace.NEPOUZITELNE_HESLO),
            sha_1=None,
        )
        self._zapocti("uzivatele", zmeneno=zmeneno)
        self.stdout.write(f"Anonymizováno uživatelů: {zmeneno}")

    def _sekce_oznamovatele(self, options):
        """
        Anonymizuje kontaktní údaje oznamovatelů.

        :param options: Pojmenované argumenty z příkazového řádku.
        """
        from oznameni.models import Oznamovatel

        k_anonymizaci = self._zaklad(Oznamovatel).exclude(email__endswith=f"@{anonymizace.ANONYM_DOMENA}")
        pocet = k_anonymizaci.count()
        self._zapocti("oznamovatele", zpracovano=pocet)
        self.stdout.write(f"Oznamovatelů k anonymizaci: {pocet}")

        if options["dry_run"]:
            return

        zmeneno = k_anonymizaci.update(
            oznamovatel=Concat(Value("oznamovatel_"), Cast("pk", TextField()), output_field=TextField()),
            odpovedna_osoba=Concat(Value("osoba_"), Cast("pk", TextField()), output_field=TextField()),
            adresa=Concat(Value("adresa_"), Cast("pk", TextField()), output_field=TextField()),
            telefon=Value(anonymizace.ANONYM_TELEFON),
            email=Concat(Cast("pk", TextField()), Value(f"@{anonymizace.ANONYM_DOMENA}"), output_field=TextField()),
            poznamka=Case(
                When(Q(poznamka__isnull=True) | Q(poznamka=""), then=F("poznamka")),
                default=Concat(Value("poznamka_"), Cast("pk", TextField()), output_field=TextField()),
                output_field=TextField(),
            ),
        )
        self._zapocti("oznamovatele", zmeneno=zmeneno)
        self.stdout.write(f"Anonymizováno oznamovatelů: {zmeneno}")

    def _sekce_logy(self, options):
        """
        Nahradí IP adresy přihlášení a adresy příjemců notifikací.

        :param options: Pojmenované argumenty z příkazového řádku.
        """
        from uzivatel.models import NotificationsLog, UzivatelPrihlaseniLog

        prihlaseni = self._zaklad(UzivatelPrihlaseniLog).exclude(ip_adresa=anonymizace.ANONYM_IP)
        notifikace = self._zaklad(NotificationsLog).exclude(receiver_address__endswith=f"@{anonymizace.ANONYM_DOMENA}")
        pocet = prihlaseni.count() + notifikace.count()
        self._zapocti("logy", zpracovano=pocet)
        self.stdout.write(f"Řádků logů k anonymizaci: {pocet}")

        if options["dry_run"]:
            return

        zmeneno = prihlaseni.update(ip_adresa=anonymizace.ANONYM_IP)
        zmeneno += notifikace.update(
            receiver_address=Concat(
                Value("notifikace_"),
                Cast("id", TextField()),
                Value(f"@{anonymizace.ANONYM_DOMENA}"),
                output_field=TextField(),
            )
        )
        self._zapocti("logy", zmeneno=zmeneno)
        self.stdout.write(f"Anonymizováno řádků logů: {zmeneno}")

    def _sekce_texty(self, options):
        """
        Zakryje chráněná textová pole podle schématu ``amcr.xsd``.

        Mění se všechny záznamy bez ohledu na přístupnost, protože zadání to tak
        vyžaduje. Prázdná pole a ``NULL`` zůstávají, aby se nezměnila struktura
        exportovaného XML.

        :param options: Pojmenované argumenty z příkazového řádku.
        """
        from django.apps import apps

        for klic_modelu, pole in anonymizace.CHRANENA_TEXTOVA_POLE.items():
            model = apps.get_model(klic_modelu)
            queryset = self._zaklad(model)

            podminka = Q()
            for _element, nazev_pole in pole:
                podminka |= ~Q(**{nazev_pole: ""}) & Q(**{f"{nazev_pole}__isnull": False})
            k_anonymizaci = queryset.filter(podminka)

            pocet = k_anonymizaci.count()
            self._zapocti("texty", zpracovano=pocet)
            self.stdout.write(f"{klic_modelu}: {pocet} záznamů s neprázdným chráněným textem")

            if options["dry_run"] or not pocet:
                continue

            zmeny = {}
            for _element, nazev_pole in pole:
                zmeny[nazev_pole] = Case(
                    When(Q(**{f"{nazev_pole}__isnull": True}) | Q(**{nazev_pole: ""}), then=F(nazev_pole)),
                    default=Concat(Value(f"{nazev_pole}_"), Cast("pk", TextField()), output_field=TextField()),
                    output_field=TextField(),
                )
            zmeneno = k_anonymizaci.update(**zmeny)
            self._zapocti("texty", zmeneno=zmeneno)

    def _sekce_pid(self, options):
        """
        Přepíše uložené hodnoty ``doi`` a ``igsn`` na prefix cílové instance.

        Hodnoty se skládají existujícími settery modelů, aby formát zůstal na
        jediném místě. Prázdný prefix znamená, že instance identifikátory neraží
        – hodnota se pak vynuluje, aby v databázi nezůstal produkční identifikátor.

        :param options: Pojmenované argumenty z příkazového řádku.
        """
        from dokument.models import Dokument
        from lokalita.models import Lokalita
        from pas.models import SamostatnyNalez

        if not settings.DOI_PREFIX or not settings.IGSN_PREFIX:
            self.stdout.write(
                self.style.WARNING(
                    "Prázdný prefix v secrets: dotčené hodnoty se vynulují, aby v databázi "
                    "nezůstal produkční identifikátor."
                )
            )
            logger.warning(
                "core.management.commands.anonymizace_dat.pid.prazdny_prefix",
                extra={"doi_prefix": settings.DOI_PREFIX, "igsn_prefix": settings.IGSN_PREFIX},
            )

        self._prepis_pid(
            self._zaklad(Dokument).exclude(doi__isnull=True).exclude(doi=""),
            "doi",
            lambda zaznam: zaznam.set_doi(),
            options,
        )
        self._prepis_pid(
            self._zaklad(Lokalita).exclude(igsn__isnull=True).exclude(igsn="").select_related("archeologicky_zaznam"),
            "igsn",
            lambda zaznam: zaznam.set_igsn(),
            options,
        )
        self._prepis_pid(
            self._zaklad(SamostatnyNalez).exclude(igsn__isnull=True).exclude(igsn=""),
            "igsn",
            lambda zaznam: zaznam.set_igsn(),
            options,
        )

    def _prepis_pid(self, queryset, nazev_pole, setter, options):
        """
        Přepíše identifikátory jednoho modelu po dávkách.

        :param queryset: Záznamy s neprázdným identifikátorem.
        :param nazev_pole: Název sloupce s identifikátorem.
        :param setter: Funkce volaná nad záznamem, která hodnotu přepočítá.
        :param options: Pojmenované argumenty z příkazového řádku.
        """
        model = queryset.model
        pocet = queryset.count()
        self._zapocti("pid", zpracovano=pocet)
        self.stdout.write(f"{model.__name__}.{nazev_pole}: {pocet} hodnot k přepisu")

        if options["dry_run"] or not pocet:
            return

        prefix_je_prazdny = not (settings.DOI_PREFIX if nazev_pole == "doi" else settings.IGSN_PREFIX)
        zmeneno = 0
        for davka in self._po_davkach(queryset, options["batch_size"]):
            for zaznam in davka:
                zaznam.suppress_signal = True
                if prefix_je_prazdny:
                    setattr(zaznam, nazev_pole, None)
                else:
                    setter(zaznam)
            with transaction.atomic():
                model.objects.bulk_update(davka, [nazev_pole])
            zmeneno += len(davka)
        self._zapocti("pid", zmeneno=zmeneno)

    def _po_davkach(self, queryset, velikost):
        """
        Prochází queryset po dávkách pomocí keyset paginace.

        Stránkování podle primárního klíče je proti ``OFFSET`` podstatně
        levnější u tabulek se statisíci řádků.

        :param queryset: Zdrojový queryset; musí mít celočíselný primární klíč.
        :param velikost: Počet záznamů v jedné dávce.
        :return: Generátor seznamů záznamů.
        """
        posledni_pk = 0
        while True:
            davka = list(queryset.filter(pk__gt=posledni_pk).order_by("pk")[:velikost])
            if not davka:
                return
            yield davka
            posledni_pk = davka[-1].pk

    def _sekce_geometrie(self, options):
        """
        Přesune polohy záznamů s přístupností vyšší než A.

        Běh drží zámek synchronizace RÚIAN, protože ta sahá na tytéž katastry
        a souběh by vedl ke ztrátě dat.

        :param options: Pojmenované argumenty z příkazového řádku.
        :raises CommandError: Pokud neodpovídají souřadnicové systémy nebo
            právě běží synchronizace RÚIAN.
        """
        from heslar.ruian_sync.zamek import ruian_sync_lock

        self._overr_srid()
        self._overr_hranice_okresu()
        self.lze_vypnout_trigger = self._lze_vypnout_trigger()
        self.generator_poloh = GeneratorPoloh()

        with ruian_sync_lock() as ziskan:
            if not ziskan:
                raise CommandError(
                    "Běží synchronizace RÚIAN, která mění tytéž katastry. Spusť anonymizaci až po jejím dokončení."
                )
            posunute_piany = self._posun_piany(options)
            self._posun_vyskove_body(posunute_piany, options)
            self._prepocti_katastry_az(posunute_piany, options)
            self._nahodne_katastry_az(posunute_piany, options)
            self._posun_body_zaznamu(options)
            self._obnov_snapshot_katastru(options)
            self._vypis_duvody()

    def _overr_srid(self):
        """
        Ověří, že geometrické sloupce leží v očekávaných souřadnicových systémech.

        Smíšené souřadnicové systémy se v prostorových dotazech neprojeví chybou,
        ale tichým prázdným výsledkem, proto je lepší běh rovnou zastavit.

        :raises CommandError: Pokud některý sloupec leží v jiném systému.
        """
        tabulky = tuple({tabulka for tabulka, _sloupec in OCEKAVANE_SRID})
        with connection.cursor() as kurzor:
            kurzor.execute(
                "SELECT f_table_name, f_geometry_column, srid FROM geometry_columns WHERE f_table_name IN %s",
                [tabulky],
            )
            skutecne = {(tabulka, sloupec): srid for tabulka, sloupec, srid in kurzor.fetchall()}

        rozdily = [
            f"{tabulka}.{sloupec}: očekáváno {srid}, v databázi {skutecne.get((tabulka, sloupec))}"
            for (tabulka, sloupec), srid in OCEKAVANE_SRID.items()
            if skutecne.get((tabulka, sloupec)) != srid
        ]
        if rozdily:
            raise CommandError(
                "Souřadnicové systémy neodpovídají očekávání (chybí migrace RÚIAN do S-JTSK?): " + "; ".join(rozdily)
            )

    def _overr_hranice_okresu(self):
        """
        Ověří, že okresy mají vyplněné hranice.

        ``RuianOkres.hranice`` je v modelu nepovinné a některé starší kopie
        databáze ho mají prázdné. Nové polohy se generují právě uvnitř hranice
        okresu, takže bez ní by se nepřesunul jediný záznam – a protože se
        záznamy bez nové polohy jen tiše přeskakují, vypadal by běh jako úspěšný.
        Proto se raději zastaví hned.

        :raises CommandError: Pokud žádný okres nemá vyplněnou hranici.
        """
        from heslar.models import RuianOkres

        celkem = RuianOkres.objects.count()
        s_hranici = RuianOkres.objects.filter(hranice__isnull=False).count()
        if s_hranici == 0:
            raise CommandError(
                f"Žádný z {celkem} okresů nemá vyplněnou hranici (ruian_okres.hranice), "
                "takže není kam polohy přesunout. Doplň hranice okresů, nebo sekci geometrie vynech."
            )
        if s_hranici < celkem:
            self.stdout.write(
                self.style.WARNING(
                    f"Hranici má jen {s_hranici} z {celkem} okresů; záznamy ve zbylých okresech se přeskočí."
                )
            )

    def _lze_vypnout_trigger(self):
        """
        Zjistí, zda lze při zápisu PIANů dočasně vypnout trigger validace.

        Vypnutí ``ALTER TABLE`` vyžaduje vlastníka tabulky nebo superuživatele.
        Když oprávnění chybí, trigger neexistuje nebo ho už někdo vypnul, běh
        pokračuje bez vypínání a PIANy s vadou zdrojové geometrie se přeskočí
        jako dřív – raději než aby padal nebo sahal na cizí nastavení.

        :return: ``True``, pokud je trigger aktivní a smíme ho vypnout.
        """
        dotaz = """
            SELECT t.tgenabled,
                   (SELECT rolsuper FROM pg_roles WHERE rolname = current_user)
                   OR pg_has_role(current_user, c.relowner, 'MEMBER')
            FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
            WHERE c.oid = 'public.pian'::regclass AND t.tgname = %s
        """
        with connection.cursor() as kurzor:
            kurzor.execute(dotaz, [TRIGGER_VALIDACE_PIANU])
            radek = kurzor.fetchone()

        if radek is None:
            return False
        stav, opravneni = radek
        if stav == "D":
            self.stdout.write(self.style.WARNING(f"Trigger {TRIGGER_VALIDACE_PIANU} je vypnutý, nechávám ho být."))
            return False
        if not opravneni:
            self.stdout.write(
                self.style.WARNING(
                    f"Chybí oprávnění vypnout trigger {TRIGGER_VALIDACE_PIANU}; PIANy s vadou "
                    "zdrojové geometrie zůstanou na původní poloze."
                )
            )
            return False
        return True

    def _nastav_trigger(self, zapnout):
        """
        Zapne nebo vypne trigger validace geometrie PIANu.

        Volá se jen uvnitř ``transaction.atomic()`` spolu se zápisem dávky.
        DDL je v PostgreSQL transakční, takže když zápis selže nebo proces
        spadne, vrátí se s rollbackem i vypnutí – trigger nemůže zůstat vypnutý.

        :param zapnout: ``True`` trigger zapne, ``False`` vypne.
        """
        prikaz = "ENABLE" if zapnout else "DISABLE"
        with connection.cursor() as kurzor:
            if zapnout:
                # Django zakládá cizí klíče jako DEFERRABLE INITIALLY DEFERRED, takže
                # změna ``zm10`` nechá kontrolu klíče čekat až na commit. PostgreSQL
                # pak odmítne ALTER TABLE hláškou „pending trigger events“. Kontroly
                # se proto vynutí hned – proběhnou stejně, jen dřív.
                kurzor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            kurzor.execute(f"ALTER TABLE public.pian {prikaz} TRIGGER {TRIGGER_VALIDACE_PIANU}")
        logger.debug(
            "core.management.commands.anonymizace_dat.trigger",
            extra={"trigger": TRIGGER_VALIDACE_PIANU, "zapnut": zapnout},
        )

    def _chranene_piany(self):
        """
        Vrátí PIANy navázané na záznam s přístupností vyšší než A.

        Záměrně se nepoužívá ``Pian.pristupnost_pom``, které vrací minimum přes
        navázané záznamy: PIAN sdílený mezi veřejnou a chráněnou akcí by pak
        zůstal na skutečné poloze a chráněná akce by nebyla anonymizovaná.

        Okres a katastr se určují z reprezentativního bodu samotného PIANu, ne
        z hlavního katastru záznamu. Záznam může mít PIANy ve více okresech
        a PIAN z jiného okresu, než leží hlavní katastr, by se jinak hledal
        v průniku cizího okresu se svým listem ZM50 – buď by se přesunul mimo
        svůj okres, nebo (při prázdném průniku) zůstal na skutečné poloze.
        Hlavní katastr záznamu slouží jen jako náhrada pro PIAN, jehož bod
        neleží v žádném katastru (typicky těsně za státní hranicí).

        :return: Seznam n-tic ``(pian_id, zm50_gid, okres_id, katastr_id, zkratka_presnosti)``.
        """
        from core.utils import reprezentativni_bod_sql

        dotaz = f"""
            WITH chranene AS (
                SELECT DISTINCT ON (p.id)
                       p.id, p.zm50, p.geom_sjtsk, k.okres AS okres_zaznamu,
                       k.id AS katastr_zaznamu, hp.zkratka
                FROM pian p
                JOIN dokumentacni_jednotka dj ON dj.pian = p.id
                JOIN archeologicky_zaznam az ON az.id = dj.archeologicky_zaznam
                JOIN heslar h ON h.id = az.pristupnost
                JOIN ruian_katastr k ON k.id = az.hlavni_katastr
                JOIN heslar hp ON hp.id = p.presnost
                WHERE h.razeni > %s
                ORDER BY p.id, az.id
            )
            SELECT c.id, c.zm50, COALESCE(kp.okres, c.okres_zaznamu),
                   COALESCE(kp.id, c.katastr_zaznamu), c.zkratka
            FROM chranene c
            LEFT JOIN LATERAL (
                SELECT kat.id, kat.okres
                FROM ruian_katastr kat
                WHERE ST_Contains(kat.hranice, {reprezentativni_bod_sql('c.geom_sjtsk')})
                LIMIT 1
            ) kp ON TRUE
            ORDER BY c.id
        """
        with connection.cursor() as kurzor:
            kurzor.execute(dotaz, [PRISTUPNOST_MIN_RAZENI])
            return kurzor.fetchall()

    def _posun_piany(self, options):
        """
        Přesune a zdeformuje geometrie chráněných PIANů.

        :param options: Pojmenované argumenty z příkazového řádku.
        :return: Slovník ``{pian_id: (dx, dy)}`` s vektory posunu pro výškové body.
            V dry-runu obsahuje všechny chráněné PIANy s hodnotou ``None``, aby
            navazující kroky mohly spočítat, kolik záznamů by se změnilo.
        """
        from pian.models import Pian

        radky = self._chranene_piany()
        self._zapocti("geometrie", zpracovano=len(radky))
        self.stdout.write(f"Chráněných PIANů: {len(radky)}")

        if options["dry_run"]:
            return dict.fromkeys(radek[0] for radek in radky)
        if not radky:
            return {}

        popis_radku = {radek[0]: radek[1:] for radek in radky}
        posunute = {}
        celkem = len(radky)
        hotovo = 0

        for davka_id in self._po_klicich(list(popis_radku), options["batch_size"]):
            piany = list(Pian.objects.filter(pk__in=davka_id))
            k_zapisu = []
            for pian in piany:
                zm50_gid, okres_id, katastr_id, zkratka = popis_radku[pian.pk]
                if zkratka == PRESNOST_KATASTR:
                    vysledek = self._nahrad_katastralni_pian(pian, zm50_gid, okres_id, katastr_id, options)
                else:
                    vysledek = self._presun_pian(pian, zm50_gid, okres_id, options)

                if vysledek is None:
                    self._zapocti("geometrie", preskoceno=1)
                    continue
                posunute[pian.pk] = vysledek
                k_zapisu.append(pian)

            if k_zapisu:
                vypnout = any(pian.pk in self.piany_s_vadou_zdroje for pian in k_zapisu)
                with transaction.atomic():
                    if vypnout:
                        self._nastav_trigger(False)
                    Pian.objects.bulk_update(k_zapisu, ["geom", "geom_sjtsk", "zm10"])
                    if vypnout:
                        self._nastav_trigger(True)
                self._zapocti("geometrie", zmeneno=len(k_zapisu))

            hotovo += len(davka_id)
            self.stdout.write(f"\rPIANy: {round(hotovo / celkem * 100)}%", ending="")

        self.stdout.write("")
        return posunute

    def _presun_pian(self, pian, zm50_gid, okres_id, options):
        """
        Najde PIANu novou polohu uvnitř původního okresu a listu ZM50.

        Omezení na původní list ZM50 drží v souladu ``Pian.ident_cely``, které
        číslo listu obsahuje, se sloupcem ``zm50``. Nastaví atributy instance,
        ale neukládá ji – zápis dělá dávkově volající.

        :param pian: Instance ``Pian`` k přesunu.
        :param zm50_gid: Identifikátor původního listu ZM50.
        :param okres_id: Primární klíč původního okresu.
        :param options: Pojmenované argumenty z příkazového řádku.
        :return: Dvojice ``(dx, dy)`` s vektorem posunu, nebo ``None`` při neúspěchu.
        """
        from pian.models import get_ZM_from_point

        stary_bod = reprezentativni_bod(pian.geom_sjtsk)
        duvod = "min_posun"

        for _pokus in range(POKUSY_POLOHY):
            novy_bod = self.generator_poloh.nova_poloha_pro_pian(okres_id, zm50_gid, stary_bod, options["min_posun_m"])
            if novy_bod is None:
                break

            dx, dy = spocitej_posun(stary_bod, novy_bod)
            nova_geom = posun_geometrii(pian.geom_sjtsk, dx, dy)
            nova_geom, deformovano = deformuj_geometrii(nova_geom, options["deformace_m"], self.generator_nahody)

            zm10, zm50 = get_ZM_from_point(reprezentativni_bod(nova_geom))
            if zm10 is None or zm50 is None or zm50.pk != zm50_gid:
                duvod = "zm_nenalezeno"
                continue

            if not self._uloz_geometrii_pianu(pian, nova_geom, zm10):
                # Mez ve WGS-84 závisí na poloze, takže jinde tentýž tvar projít může.
                duvod = "neplatna_geometrie"
                continue
            # Počítá se až u uloženého PIANu, aby zahozené pokusy o novou polohu
            # tentýž záznam nezapočítaly víckrát.
            if not deformovano and options["deformace_m"] > 0 and nova_geom.num_coords > 1:
                self._zapocti_duvod("bez_deformace", pian.ident_cely)
            return dx, dy

        logger.debug(
            "core.management.commands.anonymizace_dat.pian.bez_nove_polohy",
            extra={"pian": pian.ident_cely, "zm50": zm50_gid, "okres": okres_id, "duvod": duvod},
        )
        if duvod == "neplatna_geometrie":
            duvod = self._duvod_neplatne_geometrie(pian)
        else:
            # "min_posun" i "zm_nenalezeno" znamenají totéž: nenašla se nová poloha.
            duvod = "bez_nove_polohy"
        self._zapocti_duvod(duvod, pian.ident_cely)
        return None

    def _nahrad_katastralni_pian(self, pian, zm50_gid, okres_id, katastr_id, options):
        """
        Nahradí geometrii PIANu s přesností „katastr“ hranicí jiného katastru.

        Posouvat ani deformovat hranici katastru nedává smysl – není to citlivý
        tvar a výsledkem by byl polygon neodpovídající žádnému katastru. Vybírá
        se proto jiný katastr téhož okresu ležící v témže listu ZM50, stejně jako
        to při zakládání dělá ``pian.models.vytvor_pian``.

        :param pian: Instance ``Pian`` k záměně.
        :param zm50_gid: Identifikátor původního listu ZM50.
        :param okres_id: Primární klíč okresu.
        :param katastr_id: Primární klíč hlavního katastru záznamu; použije se jako
            náhrada, pokud se současný katastr nepodaří určit z geometrie.
        :param options: Pojmenované argumenty z příkazového řádku.
        :return: Dvojice ``(dx, dy)`` s vektorem posunu, nebo ``None`` při neúspěchu.
        """
        from core.utils import get_cadastre_from_point
        from heslar.models import RuianKatastr
        from pian.models import get_ZM_from_point

        stary_bod = reprezentativni_bod(pian.geom_sjtsk)
        # Vyloučit je potřeba katastr, jehož hranici PIAN právě nese, ne hlavní
        # katastr záznamu: ten už mohl přepsat dřívější běh a PIAN by se pak
        # mohl vrátit na svou původní hranici.
        soucasny = get_cadastre_from_point((stary_bod.x, stary_bod.y))
        kandidati = self._kandidatni_katastry(okres_id, zm50_gid, soucasny.pk if soucasny else katastr_id)
        self.generator_nahody.shuffle(kandidati)
        neplatnych = 0

        for kandidat_id in kandidati:
            katastr = RuianKatastr.objects.filter(pk=kandidat_id).first()
            if katastr is None or katastr.hranice is None:
                continue
            if not splnuje_minimalni_posun(stary_bod, reprezentativni_bod(katastr.hranice), options["min_posun_m"]):
                continue
            zm10, zm50 = get_ZM_from_point(katastr.definicni_bod)
            if zm10 is None or zm50 is None or zm50.pk != zm50_gid:
                continue
            if not self._uloz_geometrii_pianu(pian, katastr.hranice, zm10):
                # Hranice neprošla kontrolou databáze (třeba po převodu do WGS-84); zkusíme jiný katastr.
                neplatnych += 1
                continue
            return spocitej_posun(stary_bod, reprezentativni_bod(katastr.hranice))

        logger.debug(
            "core.management.commands.anonymizace_dat.pian.bez_nahradniho_katastru",
            extra={"pian": pian.ident_cely, "okres": okres_id, "zm50": zm50_gid, "neplatnych": neplatnych},
        )
        self._zapocti_duvod("neplatna_geometrie" if neplatnych else "bez_nahradniho_katastru", pian.ident_cely)
        return None

    def _duvod_neplatne_geometrie(self, pian):
        """
        Rozliší, zda pravidla databáze porušuje už původní geometrie PIANu.

        Trigger ``validate_geom_fields_trigger`` validuje celou geometrii, ne jen
        naši změnu. Část záznamů má v databázi tvar, který by dnešním pravidlům
        nevyhověl – bývá to segment kratší než povolená mez nebo linie protínající
        sama sebe. Posun délky segmentů nemění, takže u nich přesun většinou
        neprojde; deformace tvaru je občas napraví, proto to není jistá prohra.
        Rozlišení je v souhrnu důležité: napovídá, jestli hledat chybu u sebe,
        nebo ve zdrojových datech.

        :param pian: Instance ``Pian`` s původní geometrií.
        :return: Strojový název důvodu.
        """
        if not splnuje_pravidla_databaze(pian.geom_sjtsk) or self._zdroj_wgs_je_vadny(pian):
            return "zdrojova_geometrie_neplatna"
        return "neplatna_geometrie"

    @staticmethod
    def _zdroj_wgs_je_vadny(pian):
        """
        Zjistí, zda pravidla databáze porušuje původní geometrie PIANu ve WGS-84.

        Trigger kontroluje obě kopie geometrie a mez délky segmentu ve stupních
        umí porušit i tvar, který v S-JTSK projde. Chybějící hodnota se za vadu
        nepovažuje – není co převzít.

        :param pian: Instance ``Pian`` s původní geometrií.
        :return: ``True``, pokud ``pian.geom`` existuje a pravidla porušuje.
        """
        zdroj = getattr(pian, "geom", None)
        return zdroj is not None and not splnuje_pravidla_databaze(zdroj)

    def _kandidatni_katastry(self, okres_id, zm50_gid, vyloucit_id):
        """
        Vrátí katastry téhož okresu ležící v zadaném listu ZM50.

        :param okres_id: Primární klíč okresu.
        :param zm50_gid: Identifikátor listu ZM50.
        :param vyloucit_id: Primární klíč katastru, který se do výběru nezahrne.
        :return: Seznam primárních klíčů katastrů.
        """
        from core.constants import KLADYZM50

        dotaz = """
            SELECT k.id
            FROM ruian_katastr k
            JOIN kladyzm z ON z.kategorie = %s AND ST_Contains(z.the_geom, k.definicni_bod)
            WHERE k.okres = %s AND k.id <> %s AND z.gid = %s
        """
        with connection.cursor() as kurzor:
            kurzor.execute(dotaz, [KLADYZM50, okres_id, vyloucit_id, zm50_gid])
            return [radek[0] for radek in kurzor.fetchall()]

    def _uloz_geometrii_pianu(self, pian, nova_geom_sjtsk, zm10):
        """
        Nastaví PIANu novou geometrii v obou souřadnicových systémech.

        Hodnota ve WGS-84 se dopočítává aplikační transformací s korekční
        tabulkou, ne ``ST_Transform`` – jinak by se uložené souřadnice lišily
        od všeho, co zapisuje zbytek aplikace.

        :param pian: Instance ``Pian``, která se upraví na místě.
        :param nova_geom_sjtsk: Nová geometrie v EPSG:5514.
        :param zm10: Nový klad mapového listu 1:10 000.
        :return: ``True`` při úspěchu, ``False`` pokud selhala transformace.
        """
        wgs_wkt, vysledek = transform_geom_to_wgs84(nova_geom_sjtsk.wkt)
        if vysledek != "OK":
            logger.error(
                "core.management.commands.anonymizace_dat.pian.transformace_selhala",
                extra={"pian": pian.ident_cely, "vysledek": vysledek},
            )
            self._zapocti("geometrie", chyb=1)
            return False

        nova_geom_wgs = GEOSGeometry(wgs_wkt, srid=4326)
        # Trigger validate_geom_fields_trigger validuje celou geometrii, ne jen
        # naši změnu, a některé záznamy pravidla porušují už ve zdrojových datech.
        # Zápis by takový PIAN shodil, proto ho raději necháme být.
        sjtsk_ok = splnuje_pravidla_databaze(nova_geom_sjtsk)
        wgs_ok = splnuje_pravidla_databaze(nova_geom_wgs)
        if not (sjtsk_ok and wgs_ok):
            # Vadu, kterou má už produkční geometrie, zapíšeme s vypnutým triggerem:
            # nechat chráněný PIAN na skutečné poloze je horší než vadná testovací
            # geometrie. Vadu, kterou by vyrobila až anonymizace, nezapisujeme nikdy –
            # do dat se nesmí dostat nic horšího, než co je v produkci. Posuzuje se
            # zvlášť v každém souřadnicovém systému: vada ve WGS-84 je převzatá, jen
            # když ji měla i zdrojová geometrie ve WGS-84.
            sjtsk_prevzata = sjtsk_ok or not splnuje_pravidla_databaze(pian.geom_sjtsk)
            wgs_prevzata = wgs_ok or self._zdroj_wgs_je_vadny(pian)
            if not (self.lze_vypnout_trigger and sjtsk_prevzata and wgs_prevzata):
                logger.debug(
                    "core.management.commands.anonymizace_dat.pian.neplatna_geometrie",
                    extra={"pian": pian.ident_cely},
                )
                return False
            self.piany_s_vadou_zdroje.add(pian.pk)
            self._zapocti_duvod("zapsano_s_vadou_zdroje", pian.ident_cely)

        pian.suppress_signal = True
        pian.geom_sjtsk = nova_geom_sjtsk
        pian.geom = nova_geom_wgs
        pian.zm10 = zm10
        return True

    def _posun_vyskove_body(self, posunute_piany, options):
        """
        Posune výškové body spolu s jejich PIANem.

        Body dostanou týž vektor jako PIAN, takže zůstanou na svém místě vůči
        sondě, a navíc malý vlastní rozptyl – rozmístění nivelačních bodů uvnitř
        sondy je stejně identifikující jako tvar samotného PIANu. Souřadnice
        ``z`` je niveleta, tedy výška, a nemění se.

        :param posunute_piany: Slovník ``{pian_id: (dx, dy)}``; v dry-runu
            chráněné PIANy s hodnotou ``None``.
        :param options: Pojmenované argumenty z příkazového řádku.
        """
        from adb.models import VyskovyBod

        if not posunute_piany:
            return

        queryset = VyskovyBod.objects.filter(
            adb__dokumentacni_jednotka__pian_id__in=list(posunute_piany)
        ).select_related("adb__dokumentacni_jednotka")

        if options["dry_run"]:
            pocet = queryset.count()
            self._zapocti("geometrie", zpracovano=pocet)
            self.stdout.write(f"Výškových bodů u chráněných PIANů: {pocet}")
            return

        jitter = options["deformace_m"] * POMER_JITTERU_VB
        zmeneno = 0
        for davka in self._po_davkach(queryset, options["batch_size"]):
            for bod in davka:
                dx, dy = posunute_piany[bod.adb.dokumentacni_jednotka.pian_id]
                if jitter > 0:
                    dx += self.generator_nahody.uniform(-jitter, jitter)
                    dy += self.generator_nahody.uniform(-jitter, jitter)
                bod.geom = posun_bodu_3d(bod.geom, dx, dy)
            with transaction.atomic():
                VyskovyBod.objects.bulk_update(davka, ["geom"])
            zmeneno += len(davka)

        self._zapocti("geometrie", zpracovano=zmeneno, zmeneno=zmeneno)
        self.stdout.write(f"Posunuto výškových bodů: {zmeneno}")

    def _prepocti_katastry_az(self, posunute_piany, options):
        """
        Přepočítá katastry archeologických záznamů podle nových poloh PIANů.

        Výpočet přebírá ``heslar.ruian_sync.reassign.compute_az_katastr_assignment``,
        aby pravidlo zůstalo na jediném místě. Zapisuje se ale dávkově a bez
        obalových funkcí toho modulu, protože ty zakládají Fedora transakce
        a zápisy do historie, kterým se anonymizace vyhýbá.

        U chráněného záznamu, jehož PIANy se přesunuly jen zčásti, vstupují do
        výpočtu jen přesunuté PIANy. Katastry PIANů ponechaných na místě by
        jinak prozradily skutečnou polohu. Veřejný záznam sdílející přesunutý
        PIAN se počítá ze všech svých PIANů – jeho ostatní polohy jsou veřejné.

        Záznamy, u kterých se katastry přepočítaly, si příkaz pamatuje;
        ostatním chráněným záznamům přidělí náhodné katastry
        :meth:`_nahodne_katastry_az`.

        :param posunute_piany: Slovník ``{pian_id: (dx, dy)}``; v dry-runu
            chráněné PIANy s hodnotou ``None``.
        :param options: Pojmenované argumenty z příkazového řádku.
        """
        from arch_z.models import ArcheologickyZaznam, ArcheologickyZaznamKatastr
        from dj.models import DokumentacniJednotka
        from heslar.ruian_sync.reassign import compute_az_katastr_assignment

        if not posunute_piany:
            return

        zaznamy = (
            ArcheologickyZaznam.objects.filter(dokumentacni_jednotky_akce__pian_id__in=list(posunute_piany))
            .select_related("pristupnost")
            .distinct()
            .order_by("pk")
        )

        if options["dry_run"]:
            pocet = zaznamy.count()
            self._zapocti("geometrie", zpracovano=pocet)
            self.stdout.write(f"Archeologických záznamů k přepočtu katastrů: {pocet}")
            return

        zmeneno = 0
        for davka in self._po_davkach(zaznamy, options["batch_size"]):
            piany_zaznamu = {}
            for zaznam_id, pian_id in DokumentacniJednotka.objects.filter(
                archeologicky_zaznam_id__in=[zaznam.pk for zaznam in davka], pian_id__isnull=False
            ).values_list("archeologicky_zaznam_id", "pian_id"):
                piany_zaznamu.setdefault(zaznam_id, set()).add(pian_id)

            k_zapisu = []
            nove_vazby = []
            ids_davky = []
            for zaznam in davka:
                piany = piany_zaznamu.get(zaznam.pk, set())
                presunute = sorted(pian_id for pian_id in piany if pian_id in posunute_piany)
                omezit = zaznam.pristupnost.razeni > PRISTUPNOST_MIN_RAZENI and len(presunute) < len(piany)
                hlavni_id, ostatni_ids = compute_az_katastr_assignment(
                    zaznam.ident_cely, pian_ids=presunute if omezit else None
                )
                if hlavni_id is None:
                    continue
                zaznam.suppress_signal = True
                zaznam.hlavni_katastr_id = hlavni_id
                k_zapisu.append(zaznam)
                ids_davky.append(zaznam.pk)
                nove_vazby.extend(
                    ArcheologickyZaznamKatastr(archeologicky_zaznam_id=zaznam.pk, katastr_id=katastr_id)
                    for katastr_id in ostatni_ids
                )

            if not k_zapisu:
                continue
            with transaction.atomic():
                ArcheologickyZaznam.objects.bulk_update(k_zapisu, ["hlavni_katastr_id"])
                ArcheologickyZaznamKatastr.objects.filter(archeologicky_zaznam_id__in=ids_davky).delete()
                ArcheologickyZaznamKatastr.objects.bulk_create(nove_vazby, ignore_conflicts=True)
            self.az_s_prepoctenymi_katastry.update(ids_davky)
            zmeneno += len(k_zapisu)

        self._zapocti("geometrie", zpracovano=zmeneno, zmeneno=zmeneno)
        self.stdout.write(f"Přepočítáno katastrů u archeologických záznamů: {zmeneno}")

    def _nahodne_katastry_az(self, posunute_piany, options):
        """
        Přidělí náhodné katastry chráněným záznamům, které nejde přepočítat z PIANů.

        Jde o chráněné záznamy bez PIANu, se všemi PIANy ponechanými na místě
        nebo s PIANy, které neleží v žádném katastru. Hlavní i další katastry
        jsou v ``az-chranene_udajeType`` a bez náhrady by v XML zůstaly skutečné.
        Nové katastry se berou ze stejného okresu, v jakém leží původní hlavní
        katastr.

        :param posunute_piany: Slovník ``{pian_id: (dx, dy)}``; v dry-runu
            chráněné PIANy s hodnotou ``None``.
        :param options: Pojmenované argumenty z příkazového řádku.
        """
        from arch_z.models import ArcheologickyZaznam, ArcheologickyZaznamKatastr

        zaznamy = ArcheologickyZaznam.objects.filter(pristupnost__razeni__gt=PRISTUPNOST_MIN_RAZENI)

        if options["dry_run"]:
            if posunute_piany:
                zaznamy = zaznamy.exclude(dokumentacni_jednotky_akce__pian_id__in=list(posunute_piany))
            pocet = zaznamy.count()
            self._zapocti("geometrie", zpracovano=pocet)
            self.stdout.write(f"Chráněných archeologických záznamů k náhodným katastrům: {pocet}")
            return

        zmeneno = self._nahodne_katastry_zaznamu(
            zaznamy,
            ArcheologickyZaznamKatastr,
            "archeologicky_zaznam_id",
            preskocit=self.az_s_prepoctenymi_katastry,
            ponechat_hlavni={},
            options=options,
        )
        self.stdout.write(f"Náhodné katastry u chráněných archeologických záznamů: {zmeneno}")

    def _nahodne_katastry_zaznamu(self, queryset, vazba_model, nazev_fk, preskocit, ponechat_hlavni, options):
        """
        Nahradí hlavní a další katastry záznamů náhodnými katastry téhož okresu.

        Počet dalších katastrů zůstává, aby výsledek vypadal jako skutečná data.
        Nové katastry se vybírají mimo ty dosavadní, takže žádný skutečný
        katastr nezůstane, pokud má okres dost jiných katastrů.

        :param queryset: Záznamy s polem ``hlavni_katastr``.
        :param vazba_model: Model vazby na další katastry (s polem ``katastr``).
        :param nazev_fk: Název sloupce vazby odkazujícího na záznam.
        :param preskocit: Primární klíče záznamů, které se nemají měnit vůbec.
        :param ponechat_hlavni: Slovník ``{pk: původní hlavní katastr}`` záznamů,
            kterým se mění jen další katastry – hlavní katastr už odpovídá nové
            poloze. Původní hlavní katastr se z výběru vylučuje, aby se skutečná
            poloha nevrátila mezi další katastry.
        :param options: Pojmenované argumenty z příkazového řádku.
        :return: Počet změněných záznamů.
        """
        model = queryset.model
        zmeneno = 0
        for davka in self._po_davkach(queryset.select_related("hlavni_katastr"), options["batch_size"]):
            davka = [zaznam for zaznam in davka if zaznam.pk not in preskocit]
            if not davka:
                continue

            soucasne_dalsi = {}
            for zaznam_id, katastr_id in vazba_model.objects.filter(
                **{f"{nazev_fk}__in": [zaznam.pk for zaznam in davka]}
            ).values_list(nazev_fk, "katastr_id"):
                soucasne_dalsi.setdefault(zaznam_id, set()).add(katastr_id)

            k_zapisu = []
            nove_vazby = []
            for zaznam in davka:
                dalsi = soucasne_dalsi.get(zaznam.pk, set())
                okres_id = zaznam.hlavni_katastr.okres_id
                vyloucit = dalsi | {zaznam.hlavni_katastr_id}
                hlavni_id = zaznam.hlavni_katastr_id
                if zaznam.pk in ponechat_hlavni:
                    vyloucit.add(ponechat_hlavni[zaznam.pk])
                else:
                    novy = self._vyber_nahodne_katastry(okres_id, 1, vyloucit)
                    if not novy:
                        self._zapocti("geometrie", zpracovano=1, preskoceno=1)
                        self._zapocti_duvod("bez_nahodneho_katastru", zaznam.ident_cely)
                        continue
                    hlavni_id = novy[0]
                nove_dalsi = self._vyber_nahodne_katastry(okres_id, len(dalsi), vyloucit | {hlavni_id})
                zaznam.suppress_signal = True
                zaznam.hlavni_katastr_id = hlavni_id
                k_zapisu.append(zaznam)
                nove_vazby.extend(vazba_model(**{nazev_fk: zaznam.pk, "katastr_id": k}) for k in nove_dalsi)

            if not k_zapisu:
                continue
            with transaction.atomic():
                model.objects.bulk_update(k_zapisu, ["hlavni_katastr_id"])
                vazba_model.objects.filter(**{f"{nazev_fk}__in": [zaznam.pk for zaznam in k_zapisu]}).delete()
                vazba_model.objects.bulk_create(nove_vazby)
            zmeneno += len(k_zapisu)

        self._zapocti("geometrie", zpracovano=zmeneno, zmeneno=zmeneno)
        return zmeneno

    def _vyber_nahodne_katastry(self, okres_id, pocet, vyloucit):
        """
        Vybere náhodné katastry okresu mimo zadané.

        Seznam katastrů okresu se načte jednou a drží v paměti; seřazený je
        podle klíče, aby běh se stejným ``--seed`` vybral totéž.

        :param okres_id: Primární klíč okresu.
        :param pocet: Kolik katastrů vybrat.
        :param vyloucit: Primární klíče katastrů, které vybrat nelze.
        :return: Seznam primárních klíčů; kratší než ``pocet``, pokud okres
            nemá dost jiných katastrů.
        """
        from heslar.models import RuianKatastr

        if pocet <= 0:
            return []
        if okres_id not in self.katastry_okresu:
            self.katastry_okresu[okres_id] = list(
                RuianKatastr.objects.filter(okres_id=okres_id).order_by("pk").values_list("pk", flat=True)
            )
        kandidati = [katastr_id for katastr_id in self.katastry_okresu[okres_id] if katastr_id not in vyloucit]
        return self.generator_nahody.sample(kandidati, min(pocet, len(kandidati)))

    def _obnov_snapshot_katastru(self, options):
        """
        Přegeneruje textový přehled dalších katastrů u chráněných lokalit.

        ``Lokalita.dalsi_katastry_snapshot`` drží názvy katastrů jako text, takže
        by po přesunu prozrazoval původní polohu chráněného záznamu. Názvy se
        načítají jedním dotazem na dávku, ne třemi dotazy na každou lokalitu
        jako v ``Lokalita.set_snapshots``; formát textu ale sestavuje tatáž
        funkce ``Lokalita.sestav_snapshot_katastru``.

        :param options: Pojmenované argumenty z příkazového řádku.
        """
        from arch_z.models import ArcheologickyZaznamKatastr
        from lokalita.models import Lokalita

        queryset = self._zaklad(Lokalita).filter(archeologicky_zaznam__pristupnost__razeni__gt=PRISTUPNOST_MIN_RAZENI)

        if options["dry_run"]:
            pocet = queryset.count()
            self._zapocti("geometrie", zpracovano=pocet)
            self.stdout.write(f"Chráněných lokalit k přegenerování snapshotu katastrů: {pocet}")
            return

        zmeneno = 0
        for davka in self._po_davkach(queryset, options["batch_size"]):
            nazvy = {}
            for zaznam_id, nazev in (
                ArcheologickyZaznamKatastr.objects.filter(archeologicky_zaznam_id__in=[lok.pk for lok in davka])
                .order_by("katastr__nazev")
                .values_list("archeologicky_zaznam_id", "katastr__nazev")
            ):
                nazvy.setdefault(zaznam_id, []).append(nazev)
            for lokalita in davka:
                lokalita.suppress_signal = True
                lokalita.dalsi_katastry_snapshot = Lokalita.sestav_snapshot_katastru(nazvy.get(lokalita.pk, []))
            with transaction.atomic():
                Lokalita.objects.bulk_update(davka, ["dalsi_katastry_snapshot"])
            zmeneno += len(davka)

        if zmeneno:
            self.stdout.write(f"Přegenerováno snapshotů katastrů u lokalit: {zmeneno}")

    def _posun_body_zaznamu(self, options):
        """
        Přesune bodové geometrie projektů, samostatných nálezů a dokumentů.

        U projektů navíc nahradí katastry, které nová poloha neurčuje: další
        katastry všech chráněných projektů a hlavní katastr těch, které se
        nepřesunuly (nemají geometrii, nebo se pro ně nenašla nová poloha).

        :param options: Pojmenované argumenty z příkazového řádku.
        """
        from dokument.models import DokumentExtraData
        from pas.models import SamostatnyNalez
        from projekt.models import Projekt

        presunute_projekty = self._posun_bodovy_model(
            Projekt.objects.filter(
                pristupnost_snapshot__razeni__gt=PRISTUPNOST_MIN_RAZENI, geom_sjtsk__isnull=False
            ).select_related("hlavni_katastr"),
            lambda zaznam: zaznam.hlavni_katastr.okres_id,
            "hlavni_katastr_id",
            options,
        )
        self._nahodne_katastry_projektu(presunute_projekty, options)
        self._posun_bodovy_model(
            SamostatnyNalez.objects.filter(
                pristupnost__razeni__gt=PRISTUPNOST_MIN_RAZENI, geom_sjtsk__isnull=False
            ).select_related("katastr", "projekt__hlavni_katastr"),
            self._okres_samostatneho_nalezu,
            "katastr_id",
            options,
        )
        self._posun_bodovy_model(
            DokumentExtraData.objects.filter(
                dokument__pristupnost__razeni__gt=PRISTUPNOST_MIN_RAZENI, geom_sjtsk__isnull=False
            ),
            self._okres_podle_polohy,
            None,
            options,
        )

    def _nahodne_katastry_projektu(self, presunute_projekty, options):
        """
        Nahradí katastry chráněných projektů náhodnými katastry téhož okresu.

        ``projekt-chranene_udajeType`` obsahuje hlavní i další katastry. Hlavní
        katastr přesunutého projektu už odpovídá nové poloze a zůstává; další
        katastry z polohy odvodit nelze, a tak se vyberou náhodně v okrese
        nového hlavního katastru. Projekt, který se nepřesunul, dostane
        náhodný i hlavní katastr.

        :param presunute_projekty: Slovník ``{pk: původní hlavní katastr}``
            projektů s novou polohou.
        :param options: Pojmenované argumenty z příkazového řádku.
        """
        from projekt.models import Projekt, ProjektKatastr

        projekty = Projekt.objects.filter(pristupnost_snapshot__razeni__gt=PRISTUPNOST_MIN_RAZENI)

        if options["dry_run"]:
            pocet = projekty.count()
            self._zapocti("geometrie", zpracovano=pocet)
            self.stdout.write(f"Chráněných projektů k náhodným katastrům: {pocet}")
            return

        zmeneno = self._nahodne_katastry_zaznamu(
            projekty,
            ProjektKatastr,
            "projekt_id",
            preskocit=frozenset(),
            ponechat_hlavni=presunute_projekty,
            options=options,
        )
        self.stdout.write(f"Náhodné katastry u chráněných projektů: {zmeneno}")

    @staticmethod
    def _okres_samostatneho_nalezu(nalez):
        """
        Určí okres samostatného nálezu.

        Nález nemusí mít vlastní katastr, pak se použije hlavní katastr projektu.

        :param nalez: Instance ``SamostatnyNalez``.
        :return: Primární klíč okresu, nebo ``None``.
        """
        if nalez.katastr_id is not None:
            return nalez.katastr.okres_id
        if nalez.projekt_id is not None and nalez.projekt.hlavni_katastr_id is not None:
            return nalez.projekt.hlavni_katastr.okres_id
        return None

    @staticmethod
    def _okres_podle_polohy(zaznam):
        """
        Dohledá okres prostorově podle aktuální polohy záznamu.

        Používá se u dokumentů, které vlastní vazbu na katastr nemají.

        :param zaznam: Záznam s neprázdným polem ``geom_sjtsk``.
        :return: Primární klíč okresu, nebo ``None`` pro polohu mimo ČR.
        """
        from heslar.models import RuianKatastr

        katastr = RuianKatastr.objects.filter(hranice__contains=zaznam.geom_sjtsk).values("okres_id").first()
        return katastr["okres_id"] if katastr else None

    def _posun_bodovy_model(self, queryset, zjisti_okres, nazev_pole_katastru, options):
        """
        Přesune bodové geometrie jednoho modelu do náhodných poloh v okrese.

        Katastr se nedohledává pro každý záznam zvlášť, ale pro celou dávku
        jedním dotazem – prostorové vyhledání katastru je zdaleka nejdražší část
        a po záznamech by u desítek tisíc nálezů trvalo déle než všechno ostatní
        dohromady.

        :param queryset: Záznamy s neprázdnou geometrií.
        :param zjisti_okres: Funkce vracející primární klíč okresu záznamu.
        :param nazev_pole_katastru: Název pole s katastrem, nebo ``None``,
            pokud model katastr nedrží.
        :param options: Pojmenované argumenty z příkazového řádku.
        :return: Slovník ``{pk: původní hodnota pole katastru}`` přesunutých
            záznamů (``None`` u modelu bez katastru); v dry-runu prázdný.
        """
        model = queryset.model
        pocet = queryset.count()
        self._zapocti("geometrie", zpracovano=pocet)
        self.stdout.write(f"{model.__name__}: {pocet} chráněných poloh")

        presunute = {}
        if options["dry_run"] or not pocet:
            return presunute

        pole = ["geom", "geom_sjtsk"]
        if nazev_pole_katastru:
            pole.append(nazev_pole_katastru)

        zmeneno = 0
        for davka in self._po_davkach(queryset, options["batch_size"]):
            pripravene = []
            for zaznam in davka:
                poloha = self._nova_poloha_zaznamu(zaznam, zjisti_okres(zaznam), options)
                if poloha is None:
                    self._zapocti("geometrie", preskoceno=1)
                else:
                    pripravene.append((zaznam, poloha[0], poloha[1]))

            katastry = self._katastry_pro_body([bod for _z, bod, _wgs in pripravene]) if nazev_pole_katastru else None

            k_zapisu = []
            for poradi, (zaznam, bod, wgs) in enumerate(pripravene):
                puvodni_katastr = getattr(zaznam, nazev_pole_katastru) if nazev_pole_katastru else None
                if nazev_pole_katastru:
                    katastr_id = katastry[poradi]
                    if katastr_id is None:
                        self._zapocti("geometrie", preskoceno=1)
                        continue
                    setattr(zaznam, nazev_pole_katastru, katastr_id)
                presunute[zaznam.pk] = puvodni_katastr
                zaznam.suppress_signal = True
                zaznam.geom_sjtsk = bod
                zaznam.geom = wgs
                k_zapisu.append(zaznam)

            if k_zapisu:
                with transaction.atomic():
                    model.objects.bulk_update(k_zapisu, pole)
                zmeneno += len(k_zapisu)

        self._zapocti("geometrie", zmeneno=zmeneno)
        self.stdout.write(f"Přesunuto {model.__name__}: {zmeneno}")
        return presunute

    def _nova_poloha_zaznamu(self, zaznam, okres_id, options):
        """
        Vygeneruje záznamu novou bodovou polohu uvnitř zadaného okresu.

        Pouze počítá, nic na záznamu nemění – katastr se dohledává až dávkově
        a zápis dělá volající.

        :param zaznam: Záznam s poli ``geom`` a ``geom_sjtsk``.
        :param okres_id: Primární klíč okresu, ve kterém má nová poloha ležet.
        :param options: Pojmenované argumenty z příkazového řádku.
        :return: Dvojice ``(bod v EPSG:5514, bod v EPSG:4326)``, nebo ``None``,
            pokud se polohu nepodařilo najít.
        """
        if okres_id is None:
            return None

        novy_bod = self.generator_poloh.nova_poloha_v_okrese(okres_id, zaznam.geom_sjtsk, options["min_posun_m"])
        if novy_bod is None:
            return None

        wgs_wkt, vysledek = transform_geom_to_wgs84(novy_bod.wkt)
        if vysledek != "OK":
            self._zapocti("geometrie", chyb=1)
            return None
        return novy_bod, GEOSGeometry(wgs_wkt, srid=4326)

    def _katastry_pro_body(self, body):
        """
        Dohledá katastry pro celou dávku bodů jedním dotazem.

        Dělá totéž co ``core.utils.get_cadastre_from_point``, ale hromadně:
        po jednotlivých bodech vychází prostorové vyhledání na jednotky
        milisekund, což se u desítek tisíc záznamů sečte do desítek sekund.

        :param body: Seznam bodů ``Point`` v EPSG:5514.
        :return: Seznam primárních klíčů katastrů ve shodném pořadí;
            ``None`` na místech, kde bod neleží v žádném katastru.
        """
        if not body:
            return []

        dotaz = """
            SELECT k.id
            FROM unnest(%s::float8[], %s::float8[]) WITH ORDINALITY AS b(x, y, poradi)
            LEFT JOIN LATERAL (
                SELECT kat.id
                FROM public.ruian_katastr kat
                WHERE ST_Contains(kat.hranice, ST_SetSRID(ST_MakePoint(b.x, b.y), 5514))
                LIMIT 1
            ) k ON TRUE
            ORDER BY b.poradi
        """
        with connection.cursor() as kurzor:
            kurzor.execute(dotaz, [[bod.x for bod in body], [bod.y for bod in body]])
            return [radek[0] for radek in kurzor.fetchall()]

    def _po_klicich(self, klice, velikost):
        """
        Rozdělí seznam primárních klíčů na dávky.

        :param klice: Seznam primárních klíčů.
        :param velikost: Počet klíčů v jedné dávce.
        :return: Generátor seznamů klíčů.
        """
        for zacatek in range(0, len(klice), velikost):
            yield klice[zacatek : zacatek + velikost]
