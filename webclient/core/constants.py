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
OZNAMENI_PROJ: Final = 0
SCHVALENI_OZNAMENI_PROJ: Final = 1
ZAPSANI_PROJ: Final = 2
PRIHLASENI_PROJ: Final = 3
ZAHAJENI_V_TERENU_PROJ: Final = 4
UKONCENI_V_TERENU_PROJ: Final = 5
UZAVRENI_PROJ: Final = 6
NAVRZENI_KE_ZRUSENI_PROJ: Final = 7
RUSENI_PROJ: Final = 8
VRACENI_PROJ: Final = 9
# Akce
ZAPSANI_AKCE: Final = 11
ODESLANI_AKCE: Final = 12
ARCHIVACE_AKCE: Final = 13
VRACENI_AKCE: Final = 14
# Dokument
# Samostatny nalez
# Uzivatel
# Pian
# Lokalita
# Uzivatel_spoluprace
# Externi_zdroj

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
