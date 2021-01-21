from typing import Final

# Stavy

# Projekty
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
# Akce + Lokalita (archeologicke zaznamy)
ZAPSANI_AZ: Final = "AZ01"  # 1
ODESLANI_AZ: Final = "AZ12"  # 2
ARCHIVACE_AZ: Final = "AZ23"  # 3
VRACENI_AZ: Final = "AZ-1"  # New
# Dokument
ZAPSANI_DOK: Final = "D01"  # 1
ODESLANI_DOK: Final = "D12"  # 2
ARCHIVACE_DOK: Final = "D23"  # 3
VRACENI_DOK: Final = "D-1"  # New
# Samostatny nalez
# Uzivatel
# Pian
# Uzivatel_spoluprace
# Externi_zdroj

IDENTIFIKATOR_DOCASNY_PREFIX: Final = "X-"

# Typy vazeb
PROJEKT_RELATION_TYPE: Final = "projekt"
DOKUMENT_RELATION_TYPE: Final = "dokument"
SAMOSTATNY_NALEZ_RELATION_TYPE: Final = "samostatny_nalez"
UZIVATEL_RELATION_TYPE: Final = "uzivatel"  # This is for auth_user table
PIAN_RELATION_TYPE: Final = "pian"
UZIVATEL_SPOLUPRACE_RELATION_TYPE: Final = "uzivatel_spoluprace"
EXTERNI_ZDROJ_RELATION_TYPE: Final = "externi_zdroj"
ARCHEOLOGICKY_ZAZNAM_RELATION_TYPE: Final = "archeologicky_zaznam"

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
