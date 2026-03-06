import json
import logging

from core.setting_models import CustomAdminSettings
from heslar.models import Heslar
from uzivatel.models import Organizace, Osoba, User

logger = logging.getLogger(__name__)


def get_settings(item_group, item_id):
    """
    Vrací settings. v aplikaci.

    :param item_group: Parametr ``item_group`` předává se do volání ``filter()``.
    :param item_id: Identifikátor objektu ``item``.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``loads()``, slovník.
    """
    try:
        settings_query = CustomAdminSettings.objects.filter(item_group=item_group, item_id=item_id)
        if settings_query.count() > 0:
            return json.loads(settings_query.last().value)
    except Exception as e:
        logger.error("heslar.get_settings.error", extra={"error": str(e)})
    return {}


def get_id_from_database(table, heslo, ident_cely, heslarDB) -> int:
    """
    Vrátí ID položky hesláře podle mapování nebo výchozího identifikátoru.

    :param table: Parametr ``table`` pracuje se s atributy ``objects``, vstupuje do návratové hodnoty.
    :param heslo: Heslo ``heslo`` používané při vytváření nebo aktualizaci účtu.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``filter()``, ``error()``, vstupuje do návratové hodnoty.
    :param heslarDB: Parametr ``heslarDB`` se předává do volání ``filter()``, ``error()``, ovlivňuje větvení podmínek.
    :return: Vrací výsledek operace.
    """
    try:
        if heslo in heslarDB:
            heslar_obj = table.objects.filter(ident_cely=heslarDB[heslo]).values_list("pk", flat=True).first()
            if heslar_obj:
                return heslar_obj
            else:
                logger.error(
                    "heslar.get_id_from_heslar.database_error", extra={"key": heslo, "ident_cely": heslarDB[heslo]}
                )
        return table.objects.filter(ident_cely=ident_cely).values_list("pk", flat=True).get()
    except Exception as e:
        logger.error("heslar.get_id_from_heslar.error", extra={"key": heslo, "ident_cely": ident_cely, "error": str(e)})
        return None


def load_constants(model, constant_name, CONSTANTS, COMPOSITE_CONSTANTS={}):
    """
    Načte constants. v aplikaci.

    :param model: Parametr ``model`` předává se do volání ``update()``, ``get_id_from_database()``.
    :param constant_name: Textový název nebo klíč ``constant_name`` používaný v rámci operace.
    :param CONSTANTS: Mapa základních konstant používaných při inicializaci hesláře.
    :param COMPOSITE_CONSTANTS: Mapa složených konstant používaných při inicializaci hesláře.
    """
    heslarDB = get_settings("constants", constant_name)
    missing_keys = set(heslarDB.keys()) - set(CONSTANTS.keys())
    if missing_keys:
        logger.error(
            "heslar.hesla_dynamicka.load_constants.items_not_exist",
            extra={"value": constant_name, "constant": str(missing_keys)},
        )
    globals().update({key: get_id_from_database(model, key, value, heslarDB) for key, value in CONSTANTS.items()})

    heslar_group = get_settings("constants", f"{constant_name}_group")
    missing_keys = set(heslar_group.keys()) - set(COMPOSITE_CONSTANTS.keys())
    if missing_keys:
        logger.error(
            "heslar.hesla_dynamicka.load_constants_group.items_not_exist",
            extra={"value": constant_name, "constant": str(missing_keys)},
        )
    for key, values in COMPOSITE_CONSTANTS.items():
        group = []
        items = heslar_group[key] if key in heslar_group else values
        for val in items:
            index = globals().get(val)
            if index is not None:
                group.append(globals().get(val))
            else:
                logger.warning(
                    "heslar.hesla_dynamicka.load_constants_group.item_not_exist",
                    extra={"value": val, "constant": key},
                )
        globals()[key] = group


# Použité hesláře v kódu.
HESLAR_CONSTANTS = {
    "TYP_PROJEKTU_ZACHRANNY_ID": "HES-001136",
    "TYP_PROJEKTU_PRUZKUM_ID": "HES-001138",
    "TYP_PROJEKTU_BADATELSKY_ID": "HES-001137",
    "KULTURNI_PAMATKA_KP": "HES-000177",
    "KULTURNI_PAMATKA_NKP": "HES-000178",
    "KULTURNI_PAMATKA_PZ": "HES-000179",
    "KULTURNI_PAMATKA_PR": "HES-000180",
    "PRISTUPNOST_BADATEL_ID": "HES-000866",
    "PRISTUPNOST_ARCHEOLOG_ID": "HES-000867",
    "PRISTUPNOST_ANONYM_ID": "HES-000865",
    "PRISTUPNOST_ARCHIVAR_ID": "HES-000868",
    "SPECIFIKACE_DATA_PRESNE": "HES-000887",
    "TYP_DJ_SONDA_ID": "HES-001072",
    "TYP_DJ_KATASTR": "HES-001073",
    "TYP_DJ_CELEK": "HES-001070",
    "TYP_DJ_CAST": "HES-001071",
    "TYP_DJ_LOKALITA": "HES-001074",
    "GEOMETRY_PLOCHA": "HES-001135",
    "GEOMETRY_LINIE": "HES-001134",
    "GEOMETRY_BOD": "HES-001133",
    "DOKUMENT_RADA_DATA_3D": "HES-000870",
    "MATERIAL_DOKUMENTU_DIGITALNI_SOUBOR": "HES-000217",
    # Typy dokumentu povolené k zápisu
    "TYP_DOKUMENTU_NALEZOVA_ZPRAVA": "HES-001075",
    "TYP_DOKUMENTU_PRILOHA_ZPRAVY_HLASENI": "HES-001076",
    "TYP_DOKUMENTU_EXPERTNI_POSUDEK": "HES-001077",
    "TYP_DOKUMENTU_INVESTORSKA_ZPRAVA": "HES-001079",
    "TYP_DOKUMENTU_HLASENI": "HES-001080",
    "TYP_DOKUMENTU_JINY_TEXT": "HES-001081",
    "TYP_DOKUMENTU_DATA_ANALYZY_EKOFAKTU": "HES-001082",
    "TYP_DOKUMENTU_DATA_GEODETICKA": "HES-001083",
    "TYP_DOKUMENTU_DATA_GEOFYZIKALNI": "HES-001084",
    "TYP_DOKUMENTU_DATA_GNSS": "HES-001085",
    "TYP_DOKUMENTU_DATA_TERENNIHO_VYZKUMU": "HES-001086",
    "TYP_DOKUMENTU_DATA_VEKTOROVEHO_PLANU": "HES-001087",
    "TYP_DOKUMENTU_FOTOGRAFIE_KONZERVACE": "HES-001097",
    "TYP_DOKUMENTU_FOTOGRAFIE_KRAJINY": "HES-001088",
    "TYP_DOKUMENTU_FOTOGRAFIE_LOKALITY": "HES-001089",
    "TYP_DOKUMENTU_FOTOGRAFIE_OBJEKTU": "HES-001094",
    "TYP_DOKUMENTU_FOTOGRAFIE_OSOBNI": "HES-001091",
    "TYP_DOKUMENTU_FOTOGRAFIE_PRACOVNI": "HES-001093",
    "TYP_DOKUMENTU_FOTOGRAFIE_PREDMETU": "HES-001095",
    "TYP_DOKUMENTU_FOTOGRAFIE_UDALOSTI": "HES-001092",
    "TYP_DOKUMENTU_FOTOGRAFIE_VYZKUMU_SONDY": "HES-001090",
    "TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_KRAJINY": "HES-001098",
    "TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_LOKALITY": "HES-001099",
    "TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_METODY": "HES-001116",
    "TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_VYZKUMU": "HES-001100",
    "TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_PUDNICH_PRIZNAKU": "HES-001103",
    "TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_SNEZNYCH_PRIZNAKU": "HES-001104",
    "TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_STINOVYCH_PRIZNAKU": "HES-001105",
    "TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_VEGETACNICH_PRIZNAKU": "HES-001102",
    "TYP_DOKUMENTU_MIKROFOTOGRAFIE": "HES-001096",
    "TYP_DOKUMENTU_PLAN_REGIONU": "HES-001101",
    "TYP_DOKUMENTU_PLAN_LOKALITY": "HES-001106",
    "TYP_DOKUMENTU_PLAN_VYZKUMU": "HES-001107",
    "TYP_DOKUMENTU_PLAN_SONDY": "HES-001108",
    "TYP_DOKUMENTU_PLAN_OBJEKTU": "HES-001109",
    "TYP_DOKUMENTU_KRESBA_PREDMETU": "HES-001110",
    "TYP_DOKUMENTU_MAPA": "HES-001111",
    # Knihovna 3D.
    "REKONSTRUKCE_3D_ID": "HES-001113",
    "TEXTURA_3D_ID": "HES-001115",
    "DOKUMENTACE_3D_ID": "HES-001114",
    "DOKUMENT_FORMAT_3D_AUTOCAD": "HES-000152",
    "DOKUMENT_FORMAT_3D_AUTODESK_EXCHANGE": "HES-000153",
    "DOKUMENT_FORMAT_3D_BLENDER": "HES-000154",
    "DOKUMENT_FORMAT_3D_COLLADA": "HES-000155",
    "DOKUMENT_FORMAT_3D_LEICA": "HES-000156",
    "DOKUMENT_FORMAT_3D_OBJ": "HES-000157",
    "DOKUMENT_FORMAT_3D_PRINTING": "HES-000158",
    "DOKUMENT_FORMAT_3D_REVIT": "HES-000159",
    "DOKUMENT_FORMAT_3D_SKETCHUP": "HES-000160",
    "DOKUMENT_FORMAT_3D_STANFORD_PLY": "HES-000161",
    "DOKUMENT_FORMAT_3D_STEREO_LITOGRAPHY": "HES-000163",
    "DOKUMENT_FORMAT_3D_STUDIO_MAX": "HES-000164",
    "DOKUMENT_FORMAT_3D_UNIVERSAL": "HES-000162",
    "DOKUMENT_FORMAT_3D_VRML": "HES-000165",
    "DOKUMENT_FORMAT_3D_JINY": "HES-000166",
    "EXTERNI_ZDROJ_TYP_KNIHA": "HES-001117",
    "EXTERNI_ZDROJ_TYP_CAST_KNIHY": "HES-001118",
    "EXTERNI_ZDROJ_TYP_CLANEK_V_CASOPISE": "HES-001119",
    "EXTERNI_ZDROJ_TYP_CLANEK_V_NOVINACH": "HES-001120",
    "EXTERNI_ZDROJ_TYP_NEPUBLIKOVANA_ZPRAVA": "HES-001121",
    "PIAN_PRESNOST_KATASTR": "HES-000864",
    "HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRIBLIZNE": "HES-000889",
    "HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRESNE": "HES-000886",
    "JAZYK_CS": "HES-000167",
    "JAZYK_NERELEVANTNI": "HES-000174",
    "PRIMARNE_DIGITALNI": "HES-001166",
    "DOKUMENT_LICENCE_NEZNAMA": "HES-001490",
}


HESLAR_COMPOSITE_CONSTANTS = {
    "KULTURNI_PAMATKY": [
        "KULTURNI_PAMATKA_KP",
        "KULTURNI_PAMATKA_NKP",
        "KULTURNI_PAMATKA_PZ",
        "KULTURNI_PAMATKA_PR",
    ],
    "MODEL_3D_DOKUMENT_FORMATS": [
        "DOKUMENT_FORMAT_3D_AUTOCAD",
        "DOKUMENT_FORMAT_3D_AUTODESK_EXCHANGE",
        "DOKUMENT_FORMAT_3D_BLENDER",
        "DOKUMENT_FORMAT_3D_COLLADA",
        "DOKUMENT_FORMAT_3D_LEICA",
        "DOKUMENT_FORMAT_3D_OBJ",
        "DOKUMENT_FORMAT_3D_PRINTING",
        "DOKUMENT_FORMAT_3D_REVIT",
        "DOKUMENT_FORMAT_3D_SKETCHUP",
        "DOKUMENT_FORMAT_3D_STANFORD_PLY",
        "DOKUMENT_FORMAT_3D_STEREO_LITOGRAPHY",
        "DOKUMENT_FORMAT_3D_STUDIO_MAX",
        "DOKUMENT_FORMAT_3D_UNIVERSAL",
        "DOKUMENT_FORMAT_3D_VRML",
        "DOKUMENT_FORMAT_3D_JINY",
    ],
    "ALLOWED_DOKUMENT_TYPES": [
        "TYP_DOKUMENTU_NALEZOVA_ZPRAVA",
        "TYP_DOKUMENTU_PRILOHA_ZPRAVY_HLASENI",
        "TYP_DOKUMENTU_EXPERTNI_POSUDEK",
        "TYP_DOKUMENTU_INVESTORSKA_ZPRAVA",
        "TYP_DOKUMENTU_HLASENI",
        "TYP_DOKUMENTU_JINY_TEXT",
        "TYP_DOKUMENTU_DATA_ANALYZY_EKOFAKTU",
        "TYP_DOKUMENTU_DATA_GEODETICKA",
        "TYP_DOKUMENTU_DATA_GEOFYZIKALNI",
        "TYP_DOKUMENTU_DATA_GNSS",
        "TYP_DOKUMENTU_DATA_TERENNIHO_VYZKUMU",
        "TYP_DOKUMENTU_DATA_VEKTOROVEHO_PLANU",
        "TYP_DOKUMENTU_FOTOGRAFIE_KONZERVACE",
        "TYP_DOKUMENTU_FOTOGRAFIE_KRAJINY",
        "TYP_DOKUMENTU_FOTOGRAFIE_LOKALITY",
        "TYP_DOKUMENTU_FOTOGRAFIE_OBJEKTU",
        "TYP_DOKUMENTU_FOTOGRAFIE_OSOBNI",
        "TYP_DOKUMENTU_FOTOGRAFIE_PRACOVNI",
        "TYP_DOKUMENTU_FOTOGRAFIE_PREDMETU",
        "TYP_DOKUMENTU_FOTOGRAFIE_UDALOSTI",
        "TYP_DOKUMENTU_FOTOGRAFIE_VYZKUMU_SONDY",
        "TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_KRAJINY",
        "TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_LOKALITY",
        "TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_METODY",
        "TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_VYZKUMU",
        "TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_PUDNICH_PRIZNAKU",
        "TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_SNEZNYCH_PRIZNAKU",
        "TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_STINOVYCH_PRIZNAKU",
        "TYP_DOKUMENTU_LETECKA_FOTOGRAFIE_VEGETACNICH_PRIZNAKU",
        "TYP_DOKUMENTU_MIKROFOTOGRAFIE",
        "TYP_DOKUMENTU_PLAN_REGIONU",
        "TYP_DOKUMENTU_PLAN_LOKALITY",
        "TYP_DOKUMENTU_PLAN_VYZKUMU",
        "TYP_DOKUMENTU_PLAN_SONDY",
        "TYP_DOKUMENTU_PLAN_OBJEKTU",
        "TYP_DOKUMENTU_KRESBA_PREDMETU",
        "TYP_DOKUMENTU_MAPA",
    ],
    "MODEL_3D_DOKUMENT_TYPES": [
        "REKONSTRUKCE_3D_ID",
        "TEXTURA_3D_ID",
        "DOKUMENTACE_3D_ID",
    ],
}

USER_CONSTANTS = {
    "ADMIN_USER": "U-000322",
}
OSOBA_CONSTANTS = {
    "OSOBA_ANONYM": "OS-007414",
}
ORGANZACE_CONSTANTS = {
    "ORGANIZACE_OVM": "ORG-000003",
    "ORGANIZACE_AMATER": "ORG-000011",
    "ORGANIZACE_NEURCENA": "ORG-000012",
    "ORGANIZACE_ARCHEOLOG": "ORG-000013",
    "ORGANIZACE_ZAHRANICI": "ORG-000014",
    "ORGANIZACE_JINA": "ORG-000043",
    "ORGANIZACE_ZDROJ": "ORG-000055",
}

ORGANZACE_COMPOSITE_CONSTANTS = {
    "ORGANIZACE_OBECNE": [
        "ORGANIZACE_OVM",
        "ORGANIZACE_AMATER",
        "ORGANIZACE_NEURCENA",
        "ORGANIZACE_ARCHEOLOG",
        "ORGANIZACE_ZAHRANICI",
        "ORGANIZACE_JINA",
        "ORGANIZACE_ZDROJ",
    ],
}

load_constants(Heslar, "heslar", HESLAR_CONSTANTS, HESLAR_COMPOSITE_CONSTANTS)
load_constants(Organizace, "organizace", ORGANZACE_CONSTANTS, ORGANZACE_COMPOSITE_CONSTANTS)
load_constants(Osoba, "osoba", OSOBA_CONSTANTS)
load_constants(User, "user", USER_CONSTANTS)
