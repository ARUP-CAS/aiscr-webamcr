from heslar.models import Heslar


def get_id_from_heslar(ident_cely):
    try:
        pk = Heslar.objects.get(ident_cely=ident_cely).pk
        return pk
    except Exception:
        # This will happen when automated tests are run
        return int(ident_cely.replace("HES-", ""))


# Pouzite heslare v kodu
TYP_PROJEKTU_ZACHRANNY_ID = get_id_from_heslar("HES-001136")
TYP_PROJEKTU_PRUZKUM_ID = get_id_from_heslar("HES-001138")
TYP_PROJEKTU_BADATELSKY_ID = get_id_from_heslar("HES-001137")

PRISTUPNOST_BADATEL_ID = get_id_from_heslar("HES-000866")
PRISTUPNOST_ARCHEOLOG_ID = get_id_from_heslar("HES-000867")
PRISTUPNOST_ANONYM_ID = get_id_from_heslar("HES-000865")
PRISTUPNOST_ARCHIVAR_ID = get_id_from_heslar("HES-000868")

SPECIFIKACE_DATA_PRESNE = get_id_from_heslar("HES-000887")
TYP_DJ_SONDA_ID = get_id_from_heslar("HES-001072")
TYP_DJ_KATASTR = get_id_from_heslar("HES-001073")
TYP_DJ_CELEK = get_id_from_heslar("HES-001070")
TYP_DJ_CAST = get_id_from_heslar("HES-001071")
TYP_DJ_LOKALITA = get_id_from_heslar("HES-001074")

GEOMETRY_PLOCHA = get_id_from_heslar("HES-001135")
GEOMETRY_LINIE = get_id_from_heslar("HES-001134")
GEOMETRY_BOD = get_id_from_heslar("HES-001133")

DOKUMENT_RADA_DATA_3D = get_id_from_heslar("HES-000870")
MATERIAL_DOKUMENTU_DIGITALNI_SOUBOR = get_id_from_heslar("HES-000217")

# Typy dokumentu povolene pridat k akci/projektu
DATA_GPS = get_id_from_heslar("HES-001085")
EXPERTNI_POSUDEK = get_id_from_heslar("HES-001077")
HLASENI_ZAA = get_id_from_heslar("HES-001080")
TYP_DOKUMENTU_NALEZOVA_ZPRAVA = get_id_from_heslar("HES-001075")
DATA_ANALYZY_EKOFAKTORU = get_id_from_heslar("HES-001082")
INVESTORSKA_ZPRAVA = get_id_from_heslar("HES-001079")
RESTAURATORSKA_ZPRAVA = get_id_from_heslar("HES-001078")
DATA_VEKTOROVEHO_PLANU = get_id_from_heslar("HES-001087")
TEXT_JINY = get_id_from_heslar("HES-001081")
DATA_TERENNIHO_VYZKUMU = get_id_from_heslar("HES-001086")
PRILOHA_NZ_ZAA = get_id_from_heslar("HES-001076")
DATA_GEOFYZIKALNI = get_id_from_heslar("HES-001084")
DATA_GEODETICKA = get_id_from_heslar("HES-001083")
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
REKONSTRUKCE_3D_ID = get_id_from_heslar("HES-001113")
TEXTURA_3D_ID = get_id_from_heslar("HES-001115")
DOKUMENTACE_3D_ID = get_id_from_heslar("HES-001114")
MODEL_3D_DOKUMENT_TYPES = [REKONSTRUKCE_3D_ID, TEXTURA_3D_ID, DOKUMENTACE_3D_ID]

EXTERNI_ZDROJ_TYP_KNIHA = get_id_from_heslar("HES-001117")
EXTERNI_ZDROJ_TYP_CAST_KNIHY = get_id_from_heslar("HES-001118")
EXTERNI_ZDROJ_TYP_CLANEK_V_CASOPISE = get_id_from_heslar("HES-001119")
EXTERNI_ZDROJ_TYP_CLANEK_V_NOVINACH = get_id_from_heslar("HES-001120")
EXTERNI_ZDROJ_TYP_NEPUBLIKOVANA_ZPRAVA = get_id_from_heslar("HES-001121")

PIAN_PRESNOST_KATASTR = get_id_from_heslar("HES-000864")
HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRIBLIZNE = get_id_from_heslar("HES-000889")
HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRESNE = get_id_from_heslar("HES-000886")

JAZYK_CS = get_id_from_heslar("HES-000167")
PRIMARNE_DIGITALNI = get_id_from_heslar("HES-001166")
