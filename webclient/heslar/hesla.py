from typing import Final

# Pouzite heslare v kodu
TYP_PROJEKTU_ZACHRANNY_ID: Final = 1135  # 1127
TYP_PROJEKTU_PRUZKUM_ID: Final = 1136  # 1125
TYP_PROJEKTU_BADATELSKY_ID: Final = 1134  # 1126

PRISTUPNOST_BADATEL_ID: Final = 864  # 856
PRISTUPNOST_ARCHEOLOG_ID: Final = 865  # 855
PRISTUPNOST_ANONYM_ID: Final = 863  # 857
PRISTUPNOST_ARCHIVAR_ID: Final = 866  # 859

SPECIFIKACE_DATA_PRESNE: Final = 885  # 881
TYP_DJ_SONDA_ID: Final = 1070  # 1061

GEOMETRY_PLOCHA: Final = 1133  # 1122
GEOMETRY_LINIE: Final = 1132  # 1123
GEOMETRY_BOD: Final = 1131  # 1124

# Rada modelu 3D
DOKUMENT_RADA_DATA_3D: Final = 883  # 863
MATERIAL_DOKUMENTU_DIGITALNI_SOUBOR: Final = 210  # 229

# Typy dokumentu povolene pridat k akci/projektu
DATA_GPS = 1083  # 1067
EXPERTNI_POSUDEK = 1075  # 1071
HLASENI_ZAA = 1078  # 1073
TYP_DOKUMENTU_NALEZOVA_ZPRAVA: Final = 1073  # 1076
DATA_ANALYZY_EKOFAKTORU = 1080  # 1085
INVESTORSKA_ZPRAVA = 1077  # 1086
RESTAURATORSKA_ZPRAVA = 1086  # 1087
DATA_VEKTOROVEHO_PLANU = 1085  # 1088
TEXT_JINY = 1079  # 1091
DATA_TERENNIHO_VYZKUMU = 1084  # 1095
PRILOHA_NZ_ZAA = 1074  # 1097
DATA_GEOFYZIKALNI = 1082  # 1102
DATA_GEODETICKA = 1081  # 1105
ALLOWED_DOKUMENT_TYPES = [
    DATA_GPS,
    EXPERTNI_POSUDEK,
    HLASENI_ZAA,
    TYP_DOKUMENTU_NALEZOVA_ZPRAVA,
    DATA_ANALYZY_EKOFAKTORU,
    INVESTORSKA_ZPRAVA,
    RESTAURATORSKA_ZPRAVA,
    DATA_VEKTOROVEHO_PLANU,
    TEXT_JINY,
    DATA_TERENNIHO_VYZKUMU,
    PRILOHA_NZ_ZAA,
    DATA_GEOFYZIKALNI,
    DATA_GEODETICKA,
]
REKONSTRUKCE_3D_ID: Final = 1111  # 1077
TEXTURA_3D_ID: Final = 1113  # 1083
DOKUMENTACE_3D_ID: Final = 1112  # 1104
MODEL_3D_DOKUMENT_TYPES = [REKONSTRUKCE_3D_ID, TEXTURA_3D_ID, DOKUMENTACE_3D_ID]

# Nazvy heslaru
HESLAR_AKTIVITA: Final = 1
HESLAR_AREAL: Final = 2
HESLAR_AREAL_KAT: Final = 3
HESLAR_AUTORSKA_ROLE: Final = 4
HESLAR_DOHLEDNOST: Final = 5
HESLAR_LOKALITA_DRUH: Final = 6
HESLAR_LOKALITA_KAT: Final = 7
HESLAR_DOKUMENT_FORMAT: Final = 8
HESLAR_JAZYK: Final = 9
HESLAR_PAMATKOVA_OCHRANA: Final = 10
HESLAR_LETISTE: Final = 11
HESLAR_DOKUMENT_MATERIAL: Final = 12
HESLAR_DOKUMENT_NAHRADA: Final = 13
HESLAR_NALEZOVE_OKOLNOSTI: Final = 14
HESLAR_OBDOBI: Final = 15
HESLAR_OBDOBI_KAT: Final = 16
HESLAR_OBJEKT_DRUH: Final = 17
HESLAR_OBJEKT_DRUH_KAT: Final = 18
HESLAR_POCASI: Final = 19
HESLAR_ADB_PODNET: Final = 20
HESLAR_POSUDEK_TYP: Final = 21
HESLAR_PREDMET_DRUH: Final = 22
HESLAR_PREDMET_DRUH_KAT: Final = 23
HESLAR_PIAN_PRESNOST: Final = 24
HESLAR_PRISTUPNOST: Final = 25
HESLAR_DOKUMENT_RADA: Final = 26
HESLAR_DATUM_SPECIFIKACE: Final = 27
HESLAR_OBJEKT_SPECIFIKACE: Final = 28
HESLAR_OBJEKT_SPECIFIKACE_KAT: Final = 29
HESLAR_PREDMET_SPECIFIKACE: Final = 30
HESLAR_LETFOTO_TVAR: Final = 31
HESLAR_AKCE_TYP: Final = 32
HESLAR_AKCE_TYP_KAT: Final = 33
HESLAR_DJ_TYP: Final = 34
HESLAR_DOKUMENT_TYP: Final = 35
HESLAR_EXTERNI_ZDROJ_TYP: Final = 36
HESLAR_LOKALITA_TYP: Final = 37
HESLAR_NALEZ_TYP: Final = 38
HESLAR_ORGANIZACE_TYP: Final = 39
HESLAR_PIAN_TYP: Final = 40
HESLAR_PROJEKT_TYP: Final = 41
HESLAR_ADB_TYP: Final = 42
HESLAR_UDALOST_TYP: Final = 43
HESLAR_VYSKOVY_BOD_TYP: Final = 44
HESLAR_DOKUMENT_ULOZENI: Final = 45
HESLAR_DOKUMENT_ZACHOVALOST: Final = 46
HESLAR_ZEME: Final = 47
