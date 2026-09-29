"""
Zástupné hodnoty a tabulky chráněných polí pro anonymizaci databáze.

Modul drží čistou logiku příkazu ``core.management.commands.anonymizace_dat``:
generátory zástupných hodnot, predikát vyloučených účtů a mapování chráněných
údajů z ``xml_generator/definitions/amcr.xsd`` na pole modelů. Díky oddělení od
příkazu jde všechno otestovat bez databáze a generátor dokumentace
(``docs/generate_module_docs.py``) sem nesahá, protože prochází jen soubory
přímo v ``core/management/commands/``.

Konvence zástupných hodnot navazuje na dřívější ruční anonymizaci testovacího
serveru, aby anonymizovaná data vypadala stejně jako dosud: textová pole mají
tvar ``{název_pole}_{pk}``, e-maily leží v doméně ``example.cz``.
"""

#: Doména zástupných e-mailových adres. Vyhrazená pro testy, nikdy nedoručí.
ANONYM_DOMENA = "example.cz"

#: Zástupná IP adresa přihlášení, rozsah TEST-NET-3 podle RFC 5737.
ANONYM_IP = "203.0.113.1"

#: Zástupné telefonní číslo uživatele i oznamovatele. Na rozdíl od ostatních
#: polí nejde o vzor ``{pole}_{pk}`` – ``User.telefon`` i formulářové pole
#: ``OznamovatelForm.telefon`` mají validátor
#: ``core.validators.validate_phone_number``, který vyžaduje číslo platné podle
#: knihovny ``phonenumbers``. Placeholder ve tvaru ``telefon_5`` by projít
#: nemohl a každý pozdější zápis z formuláře by na něm spadl.
ANONYM_TELEFON = "+420 222 222 222"

#: Hodnota zapisovaná do ``User.password`` anonymizovaným účtům.
#:
#: Django považuje za nepoužitelné každé heslo začínající vykřičníkem
#: (``UNUSABLE_PASSWORD_PREFIX``), takže se s ním nikdo nepřihlásí. Záměrně se
#: nepoužívá ``make_password(None)``: ten za vykřičník doplňuje náhodný řetězec,
#: takže by každý běh zapsal jinou hodnotu a opakované spuštění by nebylo
#: idempotentní.
NEPOUZITELNE_HESLO = "!"

#: Řetězec v ``User.last_name`` označující umělé účty spojené se správou dat
#: (typicky organizační účty s názvem instituce v ``first_name``). Podle zadání
#: se takové účty neanonymizují.
VYJIMKA_PRIJMENI = "Anonym"

#: Chráněná textová pole podle typů ``*-chranene_udajeType`` v ``amcr.xsd``.
#: Klíč je ``app_label.ModelName``, hodnota dvojice (název elementu v XSD,
#: název pole modelu) – obojí proto, že se místy liší a test parity s XSD
#: porovnává právě názvy elementů.
#:
#: Geometrie (``gmlType``/``wktType``) a odkazy do číselníků (``vocabType``)
#: v tabulce nejsou, ty řeší sekce ``geometrie`` příkazu.
CHRANENA_TEXTOVA_POLE = {
    "projekt.Projekt": (
        ("lokalizace", "lokalizace"),
        ("parcelni_cislo", "parcelni_cislo"),
        ("kulturni_pamatka_cislo", "kulturni_pamatka_cislo"),
        ("kulturni_pamatka_popis", "kulturni_pamatka_popis"),
    ),
    "arch_z.ArcheologickyZaznam": (("uzivatelske_oznaceni", "uzivatelske_oznaceni"),),
    "arch_z.Akce": (
        ("lokalizace_okolnosti", "lokalizace_okolnosti"),
        ("souhrn_upresneni", "souhrn_upresneni"),
    ),
    "lokalita.Lokalita": (
        ("nazev", "nazev"),
        ("popis", "popis"),
        ("poznamka", "poznamka"),
    ),
    "adb.Adb": (
        ("uzivatelske_oznaceni_sondy", "uzivatelske_oznaceni_sondy"),
        ("trat", "trat"),
        ("cislo_popisne", "cislo_popisne"),
        ("parcelni_cislo", "parcelni_cislo"),
        ("poznamka", "poznamka"),
    ),
    "pas.SamostatnyNalez": (("lokalizace", "lokalizace"),),
}

#: Mapování typů ``*-chranene_udajeType`` z ``amcr.xsd`` na klíče
#: :data:`CHRANENA_TEXTOVA_POLE`. Hodnota ``None`` znamená, že typ nemá žádné
#: volné textové pole, které by zakrývala sekce ``texty``.
#:
#: Tabulka existuje kvůli testu parity se schématem: až se ``amcr.xsd`` povýší
#: a přibude v něm chráněné pole, test spadne dřív, než anonymizace tiše přestane
#: stačit.
XSD_TYP_MODELU = {
    "projekt-chranene_udajeType": "projekt.Projekt",
    "az-chranene_udajeType": "arch_z.ArcheologickyZaznam",
    "akce-chranene_udajeType": "arch_z.Akce",
    "lok-chranene_udajeType": "lokalita.Lokalita",
    "adb-chranene_udajeType": "adb.Adb",
    "pian-chranene_udajeType": None,
    "sn-chranene_udajeType": "pas.SamostatnyNalez",
}

#: Elementy, které jsou v ``amcr.xsd`` typu ``xs:string``, ale nepatří do sekce
#: ``texty`` – nastavuje je sekce ``geometrie``.
#:
#: ``zm10`` je jediný takový případ: je to číslo mapového listu, které se po
#: přesunu PIANu dopočítá z nové polohy funkcí ``pian.models.get_ZM_from_point``.
#: Přepsat ho zástupným textem nelze, protože sloupec je cizí klíč do ``kladyzm``.
#: Výjimka je tady vypsaná jmenovitě, aby ji test parity nepřehlédl mlčky.
POLE_RESENA_GEOMETRII = {
    "pian-chranene_udajeType": frozenset({"zm10"}),
}

#: Pole ``oznamovatelType`` z ``amcr.xsd``. Není to ``chranene_udajeType``, ale
#: jde o osobní údaje a zadání je řeší samostatným akceptačním kritériem.
#: ``poznamka`` je jediné nepovinné pole, ostatní jsou v DB ``NOT NULL``.
OZNAMOVATEL_POLE = (
    ("oznamovatel", "oznamovatel"),
    ("odpovedna_osoba", "odpovedna_osoba"),
    ("adresa", "adresa"),
    ("telefon", "telefon"),
    ("email", "email"),
    ("poznamka", "poznamka"),
)


def zastupny_text(nazev_pole, pk):
    """
    Sestaví zástupnou hodnotu textového pole ve tvaru ``{nazev_pole}_{pk}``.

    Hodnota je čistou funkcí primárního klíče, takže opakovaný běh příkazu
    zapíše totéž a je idempotentní bez pomocného příznaku v databázi.

    :param nazev_pole: Název pole modelu, který se stane prefixem hodnoty.
    :param pk: Primární klíč záznamu.
    :return: Zástupná hodnota jako řetězec.
    """
    return f"{nazev_pole}_{pk}"


def zastupne_jmeno(pk):
    """
    Vrací zástupné křestní jméno uživatele.

    :param pk: Primární klíč uživatele.
    :return: Řetězec ``Jméno_{pk}``.
    """
    return f"Jméno_{pk}"


def zastupne_prijmeni(pk):
    """
    Vrací zástupné příjmení uživatele.

    Vzor záměrně neobsahuje řetězec :data:`VYJIMKA_PRIJMENI`, aby anonymizovaný
    účet nespadl do výjimky pro umělé účty a druhý běh ho zpracoval znovu.

    :param pk: Primární klíč uživatele.
    :return: Řetězec ``Příjmení_{pk}``.
    """
    return f"Příjmení_{pk}"


def zastupny_email_uzivatele(pk):
    """
    Vrací zástupnou e-mailovou adresu uživatele.

    Adresa musí být unikátní, protože ``User.email`` má ``unique=True`` a slouží
    zároveň jako ``USERNAME_FIELD``; odvození z ``pk`` to zaručuje.

    :param pk: Primární klíč uživatele.
    :return: Řetězec ``uzivatel_{pk}@example.cz``.
    """
    return f"uzivatel_{pk}@{ANONYM_DOMENA}"


def zastupny_email_oznamovatele(pk):
    """
    Vrací zástupnou e-mailovou adresu oznamovatele.

    Tvar bez prefixu je převzatý z dřívější ruční anonymizace, aby se hodnoty
    na testovacím serveru nezměnily.

    :param pk: Primární klíč oznamovatele, tedy ``projekt_id``.
    :return: Řetězec ``{pk}@example.cz``.
    """
    return f"{pk}@{ANONYM_DOMENA}"


def zastupny_email_notifikace(pk):
    """
    Vrací zástupnou adresu příjemce v logu notifikací.

    :param pk: Primární klíč záznamu ``NotificationsLog``.
    :return: Řetězec ``notifikace_{pk}@example.cz``.
    """
    return f"notifikace_{pk}@{ANONYM_DOMENA}"


def je_vyjimka_prijmeni(prijmeni):
    """
    Určí, zda příjmení označuje umělý účet vyloučený z anonymizace.

    Porovnává se bez ohledu na velikost písmen, stejně jako to dělá databázový
    filtr ``last_name__icontains`` použitý v příkazu.

    :param prijmeni: Hodnota ``User.last_name``; ``None`` se bere jako neshoda.
    :return: ``True``, pokud příjmení obsahuje :data:`VYJIMKA_PRIJMENI`.
    """
    if not prijmeni:
        return False
    return VYJIMKA_PRIJMENI.casefold() in prijmeni.casefold()


def zastupny_pid(prefix, ident_cely):
    """
    Sestaví hodnotu DOI nebo IGSN s prefixem cílové instance.

    Formát odpovídá setterům ``Dokument.set_doi`` a ``Lokalita.set_igsn``.
    Prázdný prefix znamená, že instance identifikátory neraží – v tom případě
    se vrací ``None`` a volající hodnotu v databázi vynuluje, aby v ní
    nezůstal produkční identifikátor ani nevznikl nesmyslný tvar ``/D-XXXX``.

    :param prefix: Hodnota ``settings.DOI_PREFIX`` nebo ``settings.IGSN_PREFIX``.
    :param ident_cely: Identifikátor záznamu, ze kterého se hodnota skládá.
    :return: Řetězec ``{prefix}/{ident_cely}``, nebo ``None`` při prázdném prefixu.
    """
    if not prefix:
        return None
    return f"{prefix}/{ident_cely}"
