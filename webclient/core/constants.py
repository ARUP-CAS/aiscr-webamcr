from typing import Final

# KONSTANTY K PROJEKTŮM

# Stavy projektu
PROJEKT_STAV_OZNAMENY: Final = 0
PROJEKT_STAV_ZAPSANY: Final = 1
PROJEKT_STAV_PRIHLASENY: Final = 2
PROJEKT_STAV_ZAHAJENY_V_TERENU: Final = 3
PROJEKT_STAV_UKONCENY_V_TERENU: Final = 4
PROJEKT_STAV_UZAVRENY: Final = 5
PROJEKT_STAV_ARCHIVOVANY: Final = 6
PROJEKT_STAV_NAVRZEN_KE_ZRUSENI: Final = 7
PROJEKT_STAV_ZRUSENY: Final = 8
# Transakce historie
# Projekty
OZNAMENI: Final = 0
SCHVALENI_OZNAMENI: Final = 1
ZAPSANI: Final = 2
PRIHLASENI: Final = 3
ZAHAJENI_V_TERENU: Final = 4
UKONCENI_V_TERENU: Final = 5
UZAVRENI: Final = 6
NAVRZENI_KE_ZRUSENI: Final = 7
RUSENI: Final = 8
ODMITNUTI_ZRUSENI: Final = 9
VRACENI: Final = 10
# TODO Akce

IDENTIFIKATOR_DOCASNY_PREFIX: Final = "X-"

# Typy vazeb souboru
PROJEKT_RELATION_TYPE: Final = "pr"
DOKUMENT_RELATION_TYPE: Final = "do"
SAMOSTATNY_NALEZ_RELATION_TYPE: Final = "sn"
UZIVATEL_RELATION_TYPE: Final = "uz"
PIAN_RELATION_TYPE: Final = "pi"
LOKALITA_RELATION_TYPE: Final = "lo"
UZIVATEL_SPOLUPRACE_RELATION_TYPE: Final = "us"
EXTERNI_ZDROJ_RELATION_TYPE: Final = "ez"

# Typy souboru
IMPORTED_FILE: Final = "IMPORT"
GENERATED_NOTIFICATION: Final = "AGPO"  # automaticky generována projektová oznameni
PHOTO_DOCUMENTATION: Final = "FDN"  # fotodokumentace
OTHER_DOCUMENT_FILES: Final = (
    "OSD"  # ostatní soubory dokumentace pri zápisu nového dokumentu
)
OTHER_PROJECT_FILES: Final = "OSPD"  # ostatní soubory projektové dokumentace z webu
ZA_ZL_FILES: Final = (
    "AGDZZ"  # automaticky generované dokumenty z rad ZA a ZL pri archivaci projektu
)
