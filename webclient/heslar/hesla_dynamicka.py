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

# Typy dokumentu povolene k zapisu
TYP_DOKUMENTU_NALEZOVA_ZPRAVA = get_id_from_heslar("HES-001075")
TYP_DOKUMENTU_PRILOHA_ZPRAVY_HLASENI = get_id_from_heslar("HES-001076")
TYP_DOKUMENTU_EXPERTNI_POSUDEK = get_id_from_heslar("HES-001077")
TYP_DOKUMENTU_RESTAURATORSKA_ZPRAVA = get_id_from_heslar("HES-001078")
TYP_DOKUMENTU_INVESTORSKA_ZPRAVA = get_id_from_heslar("HES-001079")
TYP_DOKUMENTU_HLASENI = get_id_from_heslar("HES-001080")
TYP_DOKUMENTU_JINY_TEXT = get_id_from_heslar("HES-001081")
TYP_DOKUMENTU_DATA_ANALYZY_EKOFAKTU = get_id_from_heslar("HES-001082")
TYP_DOKUMENTU_DATA_GEODETICKA = get_id_from_heslar("HES-001083")
TYP_DOKUMENTU_DATA_GEOFYZIKALNI = get_id_from_heslar("HES-001084")
TYP_DOKUMENTU_DATA_GNSS = get_id_from_heslar("HES-001085")
TYP_DOKUMENTU_DATA_TERENNIHO_VYZKUMU = get_id_from_heslar("HES-001086")
TYP_DOKUMENTU_DATA_VEKTOROVEHO_PLANU = get_id_from_heslar("HES-001087")
TYP_DOKUMENTU_FOTOGRAFIE_KONZERVACE = get_id_from_heslar("HES-001097")
TYP_DOKUMENTU_FOTOGRAFIE_KRAJINY = get_id_from_heslar("HES-001088")
TYP_DOKUMENTU_FOTOGRAFIE_LOKALITY = get_id_from_heslar("HES-001089")
TYP_DOKUMENTU_FOTOGRAFIE_OBJEKTU = get_id_from_heslar("HES-001094")
TYP_DOKUMENTU_FOTOGRAFIE_OSOBNI = get_id_from_heslar("HES-001091")
TYP_DOKUMENTU_FOTOGRAFIE_PRACOVNI = get_id_from_heslar("HES-001093")
TYP_DOKUMENTU_FOTOGRAFIE_PREDMETU = get_id_from_heslar("HES-001095")
TYP_DOKUMENTU_FOTOGRAFIE_UDALOSTI = get_id_from_heslar("HES-001092")
TYP_DOKUMENTU_FOTOGRAFIE_VYZKUMU_SONDY = get_id_from_heslar("HES-001090")
TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_KRAJINY = get_id_from_heslar("HES-001098")
TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_LOKALITY = get_id_from_heslar("HES-001099")
TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_METODY = get_id_from_heslar("HES-001116")
TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_VYZKUMU = get_id_from_heslar("HES-001100")
TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_PUDNICH_PRIZNAKU = get_id_from_heslar("HES-001103")
TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_SNEZNYCH_PRIZNAKU = get_id_from_heslar("HES-001104")
TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_STINOVYCH_PRIZNAKU = get_id_from_heslar("HES-001105")
TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_VEGETACNICH_PRIZNAKU = get_id_from_heslar("HES-001102")
TYP_DOKUMENTU_MIKROFOTOGRAFIE = get_id_from_heslar("HES-001096")
TYP_DOKUMENTU_PLAN_REGIONU = get_id_from_heslar("HES-001101")
TYP_DOKUMENTU_PLAN_LOKALITY = get_id_from_heslar("HES-001106")
TYP_DOKUMENTU_PLAN_VYZKUMU = get_id_from_heslar("HES-001107")
TYP_DOKUMENTU_PLAN_SONDY = get_id_from_heslar("HES-001108")
TYP_DOKUMENTU_PLAN_OBJEKTU = get_id_from_heslar("HES-001109")
TYP_DOKUMENTU_KRESBA_PREDMETU = get_id_from_heslar("HES-001110")
TYP_DOKUMENTU_MAPA = get_id_from_heslar("HES-001111")
ALLOWED_DOKUMENT_TYPES = [
    TYP_DOKUMENTU_NALEZOVA_ZPRAVA,
    TYP_DOKUMENTU_PRILOHA_ZPRAVY_HLASENI,
    TYP_DOKUMENTU_EXPERTNI_POSUDEK,
    TYP_DOKUMENTU_RESTAURATORSKA_ZPRAVA,
    TYP_DOKUMENTU_INVESTORSKA_ZPRAVA,
    TYP_DOKUMENTU_HLASENI,
    TYP_DOKUMENTU_JINY_TEXT,
    TYP_DOKUMENTU_DATA_ANALYZY_EKOFAKTU,
    TYP_DOKUMENTU_DATA_GEODETICKA,
    TYP_DOKUMENTU_DATA_GEOFYZIKALNI,
    TYP_DOKUMENTU_DATA_GNSS,
    TYP_DOKUMENTU_DATA_TERENNIHO_VYZKUMU,
    TYP_DOKUMENTU_DATA_VEKTOROVEHO_PLANU,
    TYP_DOKUMENTU_FOTOGRAFIE_KONZERVACE,
    TYP_DOKUMENTU_FOTOGRAFIE_KRAJINY,
    TYP_DOKUMENTU_FOTOGRAFIE_LOKALITY,
    TYP_DOKUMENTU_FOTOGRAFIE_OBJEKTU,
    TYP_DOKUMENTU_FOTOGRAFIE_OSOBNI,
    TYP_DOKUMENTU_FOTOGRAFIE_PRACOVNI,
    TYP_DOKUMENTU_FOTOGRAFIE_PREDMETU,
    TYP_DOKUMENTU_FOTOGRAFIE_UDALOSTI,
    TYP_DOKUMENTU_FOTOGRAFIE_VYZKUMU_SONDY,
    TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_KRAJINY,
    TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_LOKALITY,
    TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_METODY,
    TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_VYZKUMU,
    TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_PUDNICH_PRIZNAKU,
    TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_SNEZNYCH_PRIZNAKU,
    TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_STINOVYCH_PRIZNAKU,
    TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_VEGETACNICH_PRIZNAKU,
    TYP_DOKUMENTU_MIKROFOTOGRAFIE,
    TYP_DOKUMENTU_PLAN_REGIONU,
    TYP_DOKUMENTU_PLAN_LOKALITY,
    TYP_DOKUMENTU_PLAN_VYZKUMU,
    TYP_DOKUMENTU_PLAN_SONDY,
    TYP_DOKUMENTU_PLAN_OBJEKTU,
    TYP_DOKUMENTU_KRESBA_PREDMETU,
    TYP_DOKUMENTU_MAPA
]

# Knihovna 3D
REKONSTRUKCE_3D_ID = get_id_from_heslar("HES-001113")
TEXTURA_3D_ID = get_id_from_heslar("HES-001115")
DOKUMENTACE_3D_ID = get_id_from_heslar("HES-001114")
MODEL_3D_DOKUMENT_TYPES = [REKONSTRUKCE_3D_ID, TEXTURA_3D_ID, DOKUMENTACE_3D_ID]

DOKUMENT_FORMAT_3D_AUTOCAD = get_id_from_heslar("HES-000152")
DOKUMENT_FORMAT_3D_AUTODESK_EXCHANGE = get_id_from_heslar("HES-000153")
DOKUMENT_FORMAT_3D_BLENDER = get_id_from_heslar("HES-000154")
DOKUMENT_FORMAT_3D_COLLADA = get_id_from_heslar("HES-000155")
DOKUMENT_FORMAT_3D_LEICA = get_id_from_heslar("HES-000156")
DOKUMENT_FORMAT_3D_OBJ = get_id_from_heslar("HES-000157")
DOKUMENT_FORMAT_3D_PRINTING = get_id_from_heslar("HES-000158")
DOKUMENT_FORMAT_3D_REVIT = get_id_from_heslar("HES-000159")
DOKUMENT_FORMAT_3D_SKETCHUP = get_id_from_heslar("HES-000160")
DOKUMENT_FORMAT_3D_STANFORD_PLY = get_id_from_heslar("HES-000161")
DOKUMENT_FORMAT_3D_STEREO_LITOGRAPHY = get_id_from_heslar("HES-000163")
DOKUMENT_FORMAT_3D_STUDIO_MAX = get_id_from_heslar("HES-000164")
DOKUMENT_FORMAT_3D_UNIVERSAL = get_id_from_heslar("HES-000162")
DOKUMENT_FORMAT_3D_VRML = get_id_from_heslar("HES-000165")
DOKUMENT_FORMAT_3D_JINY = get_id_from_heslar("HES-000166")
MODEL_3D_DOKUMENT_FORMATS = [
    DOKUMENT_FORMAT_3D_AUTOCAD,
    DOKUMENT_FORMAT_3D_AUTODESK_EXCHANGE,
    DOKUMENT_FORMAT_3D_BLENDER,
    DOKUMENT_FORMAT_3D_COLLADA,
    DOKUMENT_FORMAT_3D_LEICA,
    DOKUMENT_FORMAT_3D_OBJ,
    DOKUMENT_FORMAT_3D_PRINTING,
    DOKUMENT_FORMAT_3D_REVIT,
    DOKUMENT_FORMAT_3D_SKETCHUP,
    DOKUMENT_FORMAT_3D_STANFORD_PLY,
    DOKUMENT_FORMAT_3D_STEREO_LITOGRAPHY,
    DOKUMENT_FORMAT_3D_STUDIO_MAX,
    DOKUMENT_FORMAT_3D_UNIVERSAL,
    DOKUMENT_FORMAT_3D_VRML,
    DOKUMENT_FORMAT_3D_JINY
]


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
