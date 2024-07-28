from typing import Final

from django.utils.translation import gettext_lazy as _

# Stavy
# Projekty
PROJEKT_STAV_VYTVORENY: Final = -1  # P-1
PROJEKT_STAV_OZNAMENY: Final = 0  # P0
PROJEKT_STAV_ZAPSANY: Final = 1  # P1
PROJEKT_STAV_PRIHLASENY: Final = 2  # P2
PROJEKT_STAV_ZAHAJENY_V_TERENU: Final = 3  # P3
PROJEKT_STAV_UKONCENY_V_TERENU: Final = 4  # P4
PROJEKT_STAV_UZAVRENY: Final = 5  # P5
PROJEKT_STAV_ARCHIVOVANY: Final = 6  # P6
PROJEKT_STAV_NAVRZEN_KE_ZRUSENI: Final = 7  # P7
PROJEKT_STAV_ZRUSENY: Final = 8  # P8
# Akce + Lokalita (archeologicke zaznamy)
AZ_STAV_ZAPSANY: Final = 1  # AZ1
AZ_STAV_ODESLANY: Final = 2  # AZ2
AZ_STAV_ARCHIVOVANY: Final = 3  # AZ3
# Dokumenty
D_STAV_ZAPSANY: Final = 1  # D1
D_STAV_ODESLANY: Final = 2  # D2
D_STAV_ARCHIVOVANY: Final = 3  # D3
# Samostatny nalezy
SN_ZAPSANY: Final = 1  # SN1
SN_ODESLANY: Final = 2  # SN2
SN_POTVRZENY: Final = 3  # SN3
SN_ARCHIVOVANY: Final = 4  # SN4
# Uzivatel
# Pian
PIAN_NEPOTVRZEN: Final = 1  # PI1
PIAN_POTVRZEN: Final = 2  # PI2
# Uzivatel_spoluprace
SPOLUPRACE_NEAKTIVNI: Final = 1  # US1
SPOLUPRACE_AKTIVNI: Final = 2  # US2
# Externi zdroje
EZ_STAV_ZAPSANY: Final = 1  # EZ1
EZ_STAV_ODESLANY: Final = 2  # EZ2
EZ_STAV_POTVRZENY: Final = 3  # EZ3

# Transakce historie
# Projekty
OZNAMENI_PROJ: Final = "PX0"  # 0
SCHVALENI_OZNAMENI_PROJ: Final = "P01"  # 1
ZAPSANI_PROJ: Final = "PX1"  # 1
PRIHLASENI_PROJ: Final = "P12"  # 2
ZAHAJENI_V_TERENU_PROJ: Final = "P23"  # 3
UKONCENI_V_TERENU_PROJ: Final = "P34"  # 4
UZAVRENI_PROJ: Final = "P45"  # 5
ARCHIVACE_PROJ: Final = "P56"  # 6
NAVRZENI_KE_ZRUSENI_PROJ: Final = "P*7"  # 7
RUSENI_PROJ: Final = "P78"  # 8
VRACENI_PROJ: Final = "P-1"  # New
VRACENI_NAVRHU_ZRUSENI: Final = "P71"  # New
VRACENI_ZRUSENI: Final = "P81"  # New
RUSENI_STARE_PROJ: Final = "P18" # New
# Akce + Lokalita (archeologicke zaznamy)
ZAPSANI_AZ: Final = "AZ01"  # 1
ODESLANI_AZ: Final = "AZ12"  # 2
ARCHIVACE_AZ: Final = "AZ23"  # 3
VRACENI_AZ: Final = "AZ-1"  # New
ZMENA_AZ: Final = "AZ-2"  # New
# Dokument
ZAPSANI_DOK: Final = "D01"  # 1
ODESLANI_DOK: Final = "D12"  # 2
ARCHIVACE_DOK: Final = "D23"  # 3
VRACENI_DOK: Final = "D-1"  # New
# Samostatny nalez
ZAPSANI_SN: Final = "SN01"  # 1
ODESLANI_SN: Final = "SN12"  # 2
POTVRZENI_SN: Final = "SN23"  # 3
ARCHIVACE_SN: Final = "SN34"  # 4
VRACENI_SN: Final = "SN-1"  # 5
# Soubory
NAHRANI_SBR: Final = "SBR0"  # 0
# Uzivatel
ZMENA_HLAVNI_ROLE: Final = "HR"  # 0, 1
ZMENA_UDAJU_ADMIN: Final = "ZUA"  # 0
ZMENA_HESLA_ADMIN: Final = "ZHA"
ADMIN_UPDATE: Final = "AU"  # 0
ZMENA_UDAJU_UZIVATEL: Final = "ZUU"
ZMENA_HESLA_UZIVATEL: Final = "ZHU"
# Katastr
ZMENA_KATASTRU: Final = "KAT"

# Uzivatel
ROLE_BADATEL_ID = 1
ROLE_ARCHEOLOG_ID = 2
ROLE_ARCHIVAR_ID = 3
ROLE_ADMIN_ID = 4
ROLE_UPRAVA_TEXTU = 6
ROLE_NASTAVENI_ODSTAVKY = 8

# Pian
ZAPSANI_PIAN: Final = "PI01"
POTVRZENI_PIAN: Final = "PI12"
# Uzivatel_spoluprace
SPOLUPRACE_ZADOST: Final = "SP01"  # 1
SPOLUPRACE_AKTIVACE: Final = "SP12"  # 2, 4
SPOLUPRACE_DEAKTIVACE: Final = "SP-1"  # 3

# Externi_zdroj
ZAPSANI_EXT_ZD: Final = "EZ01"  # 1
ODESLANI_EXT_ZD: Final = "EZ12"  # 2
POTVRZENI_EXT_ZD: Final = "EZ23"  # 3
VRACENI_EXT_ZD: Final = "EZ-1"  # New

IDENTIFIKATOR_DOCASNY_PREFIX: Final = "X-"

OBLAST_CECHY = "C"
OBLAST_MORAVA = "M"
OBLAST_CHOICES = (
    (OBLAST_CECHY, _("core.constants.cechy.text")),
    (OBLAST_MORAVA, _("core.constants.morava.text")),
)

CESKY = "cs"
ANGLICKY = "en"
JAZYKY = (
    (CESKY, _("core.constants.cs.text")),
    (ANGLICKY, _("core.constants.en.text"))
)

# Typy vazeb
PROJEKT_RELATION_TYPE: Final = "projekt"
DOKUMENT_RELATION_TYPE: Final = "dokument"
SAMOSTATNY_NALEZ_RELATION_TYPE: Final = "samostatny_nalez"
UZIVATEL_RELATION_TYPE: Final = "uzivatel"  # This is for auth_user table
PIAN_RELATION_TYPE: Final = "pian"
UZIVATEL_SPOLUPRACE_RELATION_TYPE: Final = "uzivatel_spoluprace"
EXTERNI_ZDROJ_RELATION_TYPE: Final = "externi_zdroj"
ARCHEOLOGICKY_ZAZNAM_RELATION_TYPE: Final = "archeologicky_zaznam"
DOKUMENTACNI_JEDNOTKA_RELATION_TYPE: Final = "dokumentacni_jednotka"
DOKUMENT_CAST_RELATION_TYPE: Final = "dokument_cast"
SOUBOR_RELATION_TYPE: Final = "soubor"

KLADYZM10 = 1
KLADYZM25 = 2
KLADYZM50 = 3
KLADYZM100 = 4
KLADYZM200 = 5

KLADYZM_KATEGORIE = (
    (KLADYZM10, "1:10 000"),
    (KLADYZM25, "1:25 000"),
    (KLADYZM50, "1:50 000"),
    (KLADYZM100, "1:100 000"),
    (KLADYZM200, "1:200 000"),
)
# Podporovane souradnicove systemy
COORDINATE_SYSTEM = [(2, "S-JTSK (EPSG:5514)"), (1, "WGS-84 (EPSG:4326")]

DOK_MESTO = (_("core.constants.dok.mesto_praha"), _("core.constants.dok.mesto_brno"))
DOK_VE_MESTE = (_("core.constants.dok.v_praze"), _("core.constants.dok.v_brne"))
DOK_ADRESA = (_("core.constants.dok.adresa_praha"), _("core.constants.dok.adresa_brno"))
DOK_TELEFON = {
    0: _("core.constants.dok.telefon"),
    116: _("core.constants.dok.telefon_k116"),
    141: _("core.constants.dok.telefon_k141"),
    108: _("core.constants.dok.telefon_k108"),
    124: _("core.constants.dok.telefon_k124"),
    132: _("core.constants.dok.telefon_k132"),
}
DOK_EMAIL = (_("core.constants.dok.email_praha"), _("core.constants.dok.email_brno"))
DOC_KOMU = (_("core.constants.dok.komu_praha"), _("core.constants.dok.komu_brno"))
DOC_REDITEL = (
    _("core.constants.dok.reditel_praha"),
    _("core.constants.dok.reditel_brno"),
)

ORGANIZACE_MESICU_DO_ZVEREJNENI_DEFAULT = 36
ORGANIZACE_MESICU_DO_ZVEREJNENI_MAX = 1200

PERMISSIONS_IMPORT_SHEET = "URLs"
PERMISSIONS_SHEET_ZAKLADNI_NAME = "Základní"
PERMISSIONS_SHEET_STAV_NAME = "Stav"
PERMISSIONS_SHEET_VLASTNICTVI_NAME = "Vlastnictví"
PERMISSIONS_SHEET_PRISTUPNOST_NAME = "Přístupnost"
PERMISSIONS_SHEET_APP_NAME = "app"
PERMISSIONS_SHEET_URL_NAME = "URL"
PERMISSIONS_SHEET_ACTION_NAME = "action"

UDAJ_ODSTRANEN = "údaj odstraněn"  # POZOR - neměnit - po změně by se v rámci periodických úloh všechny výskyty přepisovaly znovu, tj. vznikly nové verze všech dotčených projektů
STARY_PROJEKT_ZRUSEN = "Automatické zrušení projektů starších tří let, u kterých již nelze očekávat zahájení."

PRISTUPNOST_MIN_RAZENI = 1  # Nejnižší hodnota přístupnosti podle řazení.
