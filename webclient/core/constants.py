from typing import Final

from django.utils.translation import gettext as _

# Stavy
# Projekty
PROJEKT_STAV_VYTVORENY: Final = -1
PROJEKT_STAV_OZNAMENY: Final = 0
PROJEKT_STAV_ZAPSANY: Final = 1
PROJEKT_STAV_PRIHLASENY: Final = 2
PROJEKT_STAV_ZAHAJENY_V_TERENU: Final = 3
PROJEKT_STAV_UKONCENY_V_TERENU: Final = 4
PROJEKT_STAV_UZAVRENY: Final = 5
PROJEKT_STAV_ARCHIVOVANY: Final = 6
PROJEKT_STAV_NAVRZEN_KE_ZRUSENI: Final = 7
PROJEKT_STAV_ZRUSENY: Final = 8
# Akce + Lokalita (archeologicke zaznamy)
AZ_STAV_ZAPSANY: Final = 1
AZ_STAV_ODESLANY: Final = 2
AZ_STAV_ARCHIVOVANY: Final = 3
# Dokumenty
D_STAV_ZAPSANY: Final = 1
D_STAV_ODESLANY: Final = 2
D_STAV_ARCHIVOVANY: Final = 3
# Samostatny nalezy
SN_ZAPSANY: Final = 1
SN_ODESLANY: Final = 2
SN_POTVRZENY: Final = 3
SN_ARCHIVOVANY: Final = 4
# Uzivatel
# Pian
PIAN_NEPOTVRZEN: Final = 1
PIAN_POTVRZEN: Final = 2
# Uzivatel_spoluprace
SPOLUPRACE_NEAKTIVNI: Final = 1
SPOLUPRACE_AKTIVNI: Final = 2
# Externi zdroje
EZ_STAV_ZAPSANY: Final = 1
EZ_STAV_ODESLANY: Final = 2
EZ_STAV_POTVRZENY: Final = 3

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
PRIDANI_OZNAMOVATELE_PROJ: Final = "PO1"  # New
VRACENI_NAVRHU_ZRUSENI: Final = "P71"  # New
VRACENI_ZRUSENI: Final = "P81"  # New
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
ZMENA_HLAVNI_ROLE: Final = "HR"  # 0
ZMENA_UDAJU_ADMIN: Final = "ZUA"  # 0
ADMIN_UPDATE: Final = "AU"  # 0

# Uzivatel
ROLE_BADATEL_ID = 1
ROLE_ARCHEOLOG_ID = 2
ROLE_ARCHIVAR_ID = 3
ROLE_ADMIN_ID = 4
ROLE_UPRAVA_TEXTU = 6
ROLE_NASTAVENI_ODSTAVKY = 7

# Pian
ZAPSANI_PIAN: Final = "PI01"
POTVRZENI_PIAN: Final = "PI12"
# Uzivatel_spoluprace
# TODO domluvit jak se budou resit stavy spoluprace
SPOLUPRACE_ZADOST: Final = "SP01"
SPOLUPRACE_AKTIVACE: Final = "SP12"
SPOLUPRACE_DEAKTIVACE: Final = "SP-1"

# Externi_zdroj
ZAPSANI_EXT_ZD: Final = "EZ01"  # 1
ODESLANI_EXT_ZD: Final = "EZ12"  # 2
POTVRZENI_EXT_ZD: Final = "EZ23"  # 3
VRACENI_EXT_ZD: Final = "EZ-1"  # New

IDENTIFIKATOR_DOCASNY_PREFIX: Final = "X-"

OBLAST_CECHY = "C"
OBLAST_MORAVA = "M"
OBLAST_CHOICES = (
    (OBLAST_CECHY, "Čechy"),
    (OBLAST_MORAVA, "Morava"),
)

CESKY = "cs"
ANGLICKY = "en"
JAZYKY = ((CESKY, _("Česky")), (ANGLICKY, _("Anglicky")))

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
DOKUMENT_CAST_RELATION_TYPE: Final = "dokument_cest"
SOUBOR_RELATION_TYPE: Final = "soubor"

# Typy souboru
IMPORTED_FILE: Final = "IMPORT"
GENERATED_NOTIFICATION: Final = "AGPO"  # automaticky generována projektová oznameni
PHOTO_DOCUMENTATION: Final = "FDN"  # fotodokumentace - samostatne nalezy
OTHER_DOCUMENT_FILES: Final = (
    "OSD"  # ostatní soubory dokumentace pri zápisu nového dokumentu
)
OTHER_PROJECT_FILES: Final = "OSPD"  # ostatní soubory projektové dokumentace z webu
ZA_ZL_FILES: Final = (
    "AGDZZ"  # automaticky generované dokumenty z rad ZA a ZL pri archivaci projektu
)

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
COORDINATE_SYSTEM = [(2, "S-JTSK"), (1, "WGS-84")]

DOK_MESTO = (_("constants.dok.mesto_praha"), _("constants.dok.mesto_brno"))
DOK_VE_MESTE = (_("constants.dok.v_praze"), _("constants.dok.v_brne"))
DOK_ADRESA = (_("constants.dok.adresa_praha"), _("constants.dok.adresa_brno"))
DOK_TELEFON = {
    0: _("constants.dok.telefon"),
    116: _("constants.dok.telefon_k116"),
    141: _("constants.dok.telefon_k141"),
    108: _("constants.dok.telefon_k108"),
    124: _("constants.dok.telefon_k124"),
    132: _("constants.dok.telefon_k132"),
}
DOK_EMAIL = (_("constants.dok.email_praha"), _("constants.dok.email_brno"))
DOC_KOMU = (_("constants.dok.komu_praha"), _("constants.dok.komu_brno"))
DOC_REDITEL = (_("constants.dok.reditel_praha"), _("constants.dok.reditel_brno"))


PIAN_PRESNOST_KATASTR = 862 # HES-000864

