from typing import Final

# Stavy projektu
PROJEKT_STAV_OZNAMENY: Final = 0
PROJEKT_STAV_REGISTROVANY: Final = 1
PROJEKT_STAV_PRIHLASENY: Final = 2
PROJEKT_STAV_ZAHAJENY: Final = 3
PROJEKT_STAV_UKONCENY: Final = 4
PROJEKT_STAV_NAVRZEN_K_ARCHIVACI: Final = 5
PROJEKT_STAV_ARCHIVOVANY: Final = 6
PROJEKT_STAV_NAVRZEN_KE_ZRUSENI: Final = 7
PROJEKT_STAV_ZRUSENY: Final = 8

# Typy vazeb souboru
PROJEKT_FILE_TYPE: Final = "pr"
DOKUMENT_FILE_TYPE: Final = "do"
SAMOSTATNY_NALEZ_FILE_TYPE: Final = "sn"

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
