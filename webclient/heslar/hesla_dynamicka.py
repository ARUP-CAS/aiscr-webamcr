from typing import Final
from heslar.models import Heslar

# Pouzite heslare v kodu
TYP_PROJEKTU_ZACHRANNY_ID: Final = Heslar.objects.get(ident_cely="HES-001136").pk
TYP_PROJEKTU_PRUZKUM_ID: Final = Heslar.objects.get(ident_cely="HES-001138").pk
TYP_PROJEKTU_BADATELSKY_ID: Final = Heslar.objects.get(ident_cely="HES-001137").pk

PRISTUPNOST_BADATEL_ID: Final = Heslar.objects.get(ident_cely="HES-000866").pk
PRISTUPNOST_ARCHEOLOG_ID: Final = Heslar.objects.get(ident_cely="HES-000867").pk
PRISTUPNOST_ANONYM_ID: Final = Heslar.objects.get(ident_cely="HES-000865").pk
PRISTUPNOST_ARCHIVAR_ID: Final = Heslar.objects.get(ident_cely="HES-000868").pk

SPECIFIKACE_DATA_PRESNE: Final = Heslar.objects.get(ident_cely="HES-000887").pk
TYP_DJ_SONDA_ID: Final = Heslar.objects.get(ident_cely="HES-001072").pk
TYP_DJ_KATASTR: Final = Heslar.objects.get(ident_cely="HES-001073").pk
TYP_DJ_CELEK: Final = Heslar.objects.get(ident_cely="HES-001070").pk
TYP_DJ_CAST: Final = Heslar.objects.get(ident_cely="HES-001071").pk
TYP_DJ_LOKALITA: Final = Heslar.objects.get(ident_cely="HES-001074").pk

GEOMETRY_PLOCHA: Final = Heslar.objects.get(ident_cely="HES-001135").pk
GEOMETRY_LINIE: Final = Heslar.objects.get(ident_cely="HES-001134").pk
GEOMETRY_BOD: Final = Heslar.objects.get(ident_cely="HES-001133").pk

# Rada modelu 3D
DOKUMENT_RADA_DATA_3D: Final = Heslar.objects.get(ident_cely="HES-000870").pk
MATERIAL_DOKUMENTU_DIGITALNI_SOUBOR: Final = Heslar.objects.get(ident_cely="HES-000217").pk

# Typy dokumentu povolene pridat k akci/projektu
DATA_GPS = Heslar.objects.get(ident_cely="HES-001085").pk
EXPERTNI_POSUDEK = Heslar.objects.get(ident_cely="HES-001077").pk
HLASENI_ZAA = Heslar.objects.get(ident_cely="HES-001080").pk
TYP_DOKUMENTU_NALEZOVA_ZPRAVA: Final = Heslar.objects.get(ident_cely="HES-001075").pk
DATA_ANALYZY_EKOFAKTORU = Heslar.objects.get(ident_cely="HES-001082").pk
INVESTORSKA_ZPRAVA = Heslar.objects.get(ident_cely="HES-001079").pk
RESTAURATORSKA_ZPRAVA = Heslar.objects.get(ident_cely="HES-001078").pk
DATA_VEKTOROVEHO_PLANU = Heslar.objects.get(ident_cely="HES-001087").pk
TEXT_JINY = Heslar.objects.get(ident_cely="HES-001081").pk
DATA_TERENNIHO_VYZKUMU = Heslar.objects.get(ident_cely="HES-001086").pk
PRILOHA_NZ_ZAA = Heslar.objects.get(ident_cely="HES-001076").pk
DATA_GEOFYZIKALNI = Heslar.objects.get(ident_cely="HES-001084").pk
DATA_GEODETICKA = Heslar.objects.get(ident_cely="HES-001083").pk
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
REKONSTRUKCE_3D_ID: Final = Heslar.objects.get(ident_cely="HES-001113").pk
TEXTURA_3D_ID: Final = Heslar.objects.get(ident_cely="HES-001115").pk
DOKUMENTACE_3D_ID: Final = Heslar.objects.get(ident_cely="HES-001114").pk
MODEL_3D_DOKUMENT_TYPES = [REKONSTRUKCE_3D_ID, TEXTURA_3D_ID, DOKUMENTACE_3D_ID]

# Externi zdroj typ
EXTERNI_ZDROJ_TYP_KNIHA = Heslar.objects.get(ident_cely="HES-001117").pk
EXTERNI_ZDROJ_TYP_CAST_KNIHY = Heslar.objects.get(ident_cely="HES-001118").pk
EXTERNI_ZDROJ_TYP_CLANEK_V_CASOPISE = Heslar.objects.get(ident_cely="HES-001119").pk
EXTERNI_ZDROJ_TYP_CLANEK_V_NOVINACH = Heslar.objects.get(ident_cely="HES-001120").pk
EXTERNI_ZDROJ_TYP_NEPUBLIKOVANA_ZPRAVA = Heslar.objects.get(ident_cely="HES-001121").pk

PIAN_PRESNOST_KATASTR = Heslar.objects.get(ident_cely="HES-000864").pk
HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRIBLIZNE = Heslar.objects.get(ident_cely="HES-000889").pk
HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRESNE = Heslar.objects.get(ident_cely="HES-000886").pk
