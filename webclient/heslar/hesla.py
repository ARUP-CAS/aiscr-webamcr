from typing import Final

# Pouzite heslare v kodu
TYP_PROJEKTU_ZACHRANNY_ID: Final = 1135  # HES-001136
TYP_PROJEKTU_PRUZKUM_ID: Final = 1136  # HES-001138
TYP_PROJEKTU_BADATELSKY_ID: Final = 1134  # HES-001137

PRISTUPNOST_BADATEL_ID: Final = 864  # HES-000866
PRISTUPNOST_ARCHEOLOG_ID: Final = 865  # HES-000867
PRISTUPNOST_ANONYM_ID: Final = 863  # HES-000865
PRISTUPNOST_ARCHIVAR_ID: Final = 866  # HES-000868

SPECIFIKACE_DATA_PRESNE: Final = 885  # HES-000887
TYP_DJ_SONDA_ID: Final = 1070  # HES-001072
TYP_DJ_KATASTR: Final = 1071 # HES-001073
TYP_DJ_CELEK: Final = 1068 # HES-001070
TYP_DJ_CAST: Final = 1069 # HES-001071
TYP_DJ_LOKALITA: Final = 1072 # HES-001074

GEOMETRY_PLOCHA: Final = 1133  # HES-001135
GEOMETRY_LINIE: Final = 1132  # HES-001134
GEOMETRY_BOD: Final = 1131  # HES-001133

# Rada modelu 3D
DOKUMENT_RADA_DATA_3D: Final = 883  # HES-000870
MATERIAL_DOKUMENTU_DIGITALNI_SOUBOR: Final = 210  # HES-000217

# Typy dokumentu povolene pridat k akci/projektu
DATA_GPS = 1083  # HES-001085
EXPERTNI_POSUDEK = 1075  # HES-001077
HLASENI_ZAA = 1078  # HES-001080
TYP_DOKUMENTU_NALEZOVA_ZPRAVA: Final = 1073  # HES-001075
DATA_ANALYZY_EKOFAKTORU = 1080  # HES-001082
INVESTORSKA_ZPRAVA = 1077  # HES-001079
RESTAURATORSKA_ZPRAVA = 1086  # HES-001078
DATA_VEKTOROVEHO_PLANU = 1085  # HES-001087
TEXT_JINY = 1079  # HES-001081
DATA_TERENNIHO_VYZKUMU = 1084  # HES-001086
PRILOHA_NZ_ZAA = 1074  # HES-001076
DATA_GEOFYZIKALNI = 1082  # HES-001084
DATA_GEODETICKA = 1081  # HES-001083
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
REKONSTRUKCE_3D_ID: Final = 1111  # HES-001113
TEXTURA_3D_ID: Final = 1113  # HES-001115
DOKUMENTACE_3D_ID: Final = 1112  # HES-001114
MODEL_3D_DOKUMENT_TYPES = [REKONSTRUKCE_3D_ID, TEXTURA_3D_ID, DOKUMENTACE_3D_ID]

# Nazvy heslaru
HESLAR_AKTIVITA: Final = 1
HESLAR_AREAL: Final = 2
HESLAR_AREAL_KAT: Final = 3
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
HESLAR_JISTOTA_URCENI: Final = 48
HESLAR_STAV_DOCHOVANI: Final = 49

# Externi zdroj typ
EXTERNI_ZDROJ_TYP_KNIHA = 1115
EXTERNI_ZDROJ_TYP_CAST_KNIHY = 1116
EXTERNI_ZDROJ_TYP_CLANEK_V_CASOPISE = 1117
EXTERNI_ZDROJ_TYP_CLANEK_V_NOVINACH = 1118
EXTERNI_ZDROJ_TYP_NEPUBLIKOVANA_ZPRAVA = 1119

PIAN_PRESNOST_KATASTR = 862  # HES-000864
HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRIBLIZNE = 887  # HES-000889
HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRESNE = 884  # HES-000886
