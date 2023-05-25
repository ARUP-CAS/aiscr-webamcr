from typing import Final

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
EXTERNI_ZDROJ_TYP_KNIHA = Heslar.objects.get(ident_cely="HES-001117").pk
EXTERNI_ZDROJ_TYP_CAST_KNIHY = Heslar.objects.get(ident_cely="HES-001118").pk
EXTERNI_ZDROJ_TYP_CLANEK_V_CASOPISE = Heslar.objects.get(ident_cely="HES-001119").pk
EXTERNI_ZDROJ_TYP_CLANEK_V_NOVINACH = Heslar.objects.get(ident_cely="HES-001120").pk
EXTERNI_ZDROJ_TYP_NEPUBLIKOVANA_ZPRAVA = Heslar.objects.get(ident_cely="HES-001121").pk

PIAN_PRESNOST_KATASTR = Heslar.objects.get(ident_cely="HES-000864").pk
HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRIBLIZNE = Heslar.objects.get(ident_cely="HES-000889").pk
HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRESNE = Heslar.objects.get(ident_cely="HES-000886").pk
