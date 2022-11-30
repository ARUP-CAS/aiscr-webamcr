# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.contrib.gis.db import models


class Adb(models.Model):
    dokumentacni_jednotka = models.OneToOneField(
        "DokumentacniJednotka",
        models.DO_NOTHING,
        db_column="dokumentacni_jednotka",
        primary_key=True,
    )
    ident_cely = models.TextField(unique=True)
    typ_sondy = models.ForeignKey(
        "Heslar", models.DO_NOTHING, db_column="typ_sondy", blank=True, null=True
    )
    trat = models.TextField(blank=True, null=True)
    parcelni_cislo = models.TextField(blank=True, null=True)
    podnet = models.ForeignKey(
        "Heslar", models.DO_NOTHING, db_column="podnet", blank=True, null=True
    )
    uzivatelske_oznaceni_sondy = models.TextField(blank=True, null=True)
    stratigraficke_jednotky = models.TextField(blank=True, null=True)
    poznamka = models.TextField(blank=True, null=True)
    cislo_popisne = models.TextField(blank=True, null=True)
    autor_popisu = models.ForeignKey(
        "Osoba", models.DO_NOTHING, db_column="autor_popisu"
    )
    rok_popisu = models.IntegerField()
    autor_revize = models.ForeignKey(
        "Osoba", models.DO_NOTHING, db_column="autor_revize", blank=True, null=True
    )
    rok_revize = models.IntegerField(blank=True, null=True)
    final_cj = models.BooleanField()
    sm5 = models.ForeignKey("Kladysm5", models.DO_NOTHING, db_column="sm5")

    class Meta:
        managed = False
        db_table = "adb"


class AdbSekvence(models.Model):
    kladysm5 = models.OneToOneField("Kladysm5", models.DO_NOTHING)
    sekvence = models.IntegerField()

    class Meta:
        managed = False
        db_table = "adb_sekvence"


class Akce(models.Model):
    id = models.AutoField()
    typ = models.CharField(max_length=1, blank=True, null=True)
    lokalizace_okolnosti = models.TextField(blank=True, null=True)
    specifikace_data = models.ForeignKey(
        "Heslar", models.DO_NOTHING, db_column="specifikace_data"
    )
    hlavni_typ = models.ForeignKey(
        "Heslar", models.DO_NOTHING, db_column="hlavni_typ", blank=True, null=True
    )
    vedlejsi_typ = models.ForeignKey(
        "Heslar", models.DO_NOTHING, db_column="vedlejsi_typ", blank=True, null=True
    )
    souhrn_upresneni = models.TextField(blank=True, null=True)
    ulozeni_nalezu = models.TextField(blank=True, null=True)
    datum_ukonceni = models.TextField(blank=True, null=True)
    datum_zahajeni = models.TextField(blank=True, null=True)
    datum_zahajeni_v = models.DateField(blank=True, null=True)
    datum_ukonceni_v = models.DateField(blank=True, null=True)
    je_nz = models.BooleanField()
    final_cj = models.BooleanField()
    projekt = models.ForeignKey(
        "Projekt", models.DO_NOTHING, db_column="projekt", blank=True, null=True
    )
    ulozeni_dokumentace = models.TextField(blank=True, null=True)
    archeologicky_zaznam = models.OneToOneField(
        "ArcheologickyZaznam",
        models.DO_NOTHING,
        db_column="archeologicky_zaznam",
        primary_key=True,
    )
    odlozena_nz = models.BooleanField()

    class Meta:
        managed = False
        db_table = "akce"


class AkceVedouci(models.Model):
    akce = models.OneToOneField(
        Akce, models.DO_NOTHING, db_column="akce", primary_key=True
    )
    vedouci = models.ForeignKey("Osoba", models.DO_NOTHING, db_column="vedouci")
    organizace = models.ForeignKey(
        "Organizace", models.DO_NOTHING, db_column="organizace", blank=True, null=True
    )
    hlavni = models.BooleanField()

    class Meta:
        managed = False
        db_table = "akce_vedouci"
        unique_together = (("akce", "vedouci"),)


class ArcheologickyZaznam(models.Model):
    typ_zaznamu = models.TextField()
    pristupnost = models.ForeignKey(
        "Heslar", models.DO_NOTHING, db_column="pristupnost"
    )
    ident_cely = models.TextField(unique=True)
    stav_stary = models.SmallIntegerField()
    historie = models.ForeignKey(
        "HistorieVazby", models.DO_NOTHING, db_column="historie"
    )
    uzivatelske_oznaceni = models.TextField(blank=True, null=True)
    stav = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = "archeologicky_zaznam"


class ArcheologickyZaznamKatastr(models.Model):
    archeologicky_zaznam = models.OneToOneField(
        ArcheologickyZaznam,
        models.DO_NOTHING,
        db_column="archeologicky_zaznam",
        primary_key=True,
    )
    katastr = models.ForeignKey("RuianKatastr", models.DO_NOTHING, db_column="katastr")
    hlavni = models.BooleanField()

    class Meta:
        managed = False
        db_table = "archeologicky_zaznam_katastr"
        unique_together = (("archeologicky_zaznam", "katastr"),)


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = "auth_group"


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey("AuthPermission", models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "auth_group_permissions"
        unique_together = (("group", "permission"),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey("DjangoContentType", models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "auth_permission"
        unique_together = (("content_type", "codename"),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    ident_cely = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    osoba = models.ForeignKey(
        "Osoba", models.DO_NOTHING, db_column="osoba", blank=True, null=True
    )
    auth_level = models.IntegerField(blank=True, null=True)
    organizace = models.ForeignKey(
        "Organizace", models.DO_NOTHING, db_column="organizace"
    )
    historie = models.ForeignKey(
        "HistorieVazby", models.DO_NOTHING, db_column="historie", blank=True, null=True
    )
    email_potvrzen = models.TextField(blank=True, null=True)
    jazyk = models.CharField(max_length=15, blank=True, null=True)
    sha_1 = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "auth_user"


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "auth_user_groups"
        unique_together = (("user", "group"),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "auth_user_user_permissions"
        unique_together = (("user", "permission"),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey(
        "DjangoContentType", models.DO_NOTHING, blank=True, null=True
    )
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "django_admin_log"


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "django_content_type"
        unique_together = (("app_label", "model"),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "django_migrations"


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "django_session"


class Dokument(models.Model):
    let = models.ForeignKey(
        "Let", models.DO_NOTHING, db_column="let", blank=True, null=True
    )
    rada = models.ForeignKey("Heslar", models.DO_NOTHING, db_column="rada")
    typ_dokumentu = models.ForeignKey(
        "Heslar", models.DO_NOTHING, db_column="typ_dokumentu"
    )
    organizace = models.ForeignKey(
        "Organizace", models.DO_NOTHING, db_column="organizace"
    )
    rok_vzniku = models.IntegerField(blank=True, null=True)
    pristupnost = models.ForeignKey(
        "Heslar", models.DO_NOTHING, db_column="pristupnost"
    )
    material_originalu = models.ForeignKey(
        "Heslar", models.DO_NOTHING, db_column="material_originalu"
    )
    popis = models.TextField(blank=True, null=True)
    poznamka = models.TextField(blank=True, null=True)
    ulozeni_originalu = models.ForeignKey(
        "Heslar",
        models.DO_NOTHING,
        db_column="ulozeni_originalu",
        blank=True,
        null=True,
    )
    oznaceni_originalu = models.TextField(blank=True, null=True)
    stav = models.SmallIntegerField()
    ident_cely = models.TextField(unique=True, blank=True, null=True)
    final_cj = models.BooleanField()
    datum_zverejneni = models.DateField(blank=True, null=True)
    soubory = models.ForeignKey(
        "SouborVazby", models.DO_NOTHING, db_column="soubory", blank=True, null=True
    )
    historie = models.ForeignKey(
        "HistorieVazby", models.DO_NOTHING, db_column="historie", blank=True, null=True
    )
    licence = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "dokument"


class DokumentAutor(models.Model):
    dokument = models.OneToOneField(
        Dokument, models.DO_NOTHING, db_column="dokument", primary_key=True
    )
    autor = models.ForeignKey("Osoba", models.DO_NOTHING, db_column="autor")
    poradi = models.IntegerField()

    class Meta:
        managed = False
        db_table = "dokument_autor"
        unique_together = (("dokument", "autor"),)


class DokumentCast(models.Model):
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam,
        models.DO_NOTHING,
        db_column="archeologicky_zaznam",
        blank=True,
        null=True,
    )
    poznamka = models.TextField(blank=True, null=True)
    dokument = models.ForeignKey(Dokument, models.DO_NOTHING, db_column="dokument")
    ident_cely = models.TextField(unique=True)
    komponenty = models.OneToOneField(
        "KomponentaVazby",
        models.DO_NOTHING,
        db_column="komponenty",
        blank=True,
        null=True,
    )

    class Meta:
        managed = False
        db_table = "dokument_cast"


class DokumentExtraData(models.Model):
    dokument = models.OneToOneField(
        Dokument, models.DO_NOTHING, db_column="dokument", primary_key=True
    )
    datum_vzniku = models.DateTimeField(blank=True, null=True)
    zachovalost = models.ForeignKey(
        "Heslar", models.DO_NOTHING, db_column="zachovalost", blank=True, null=True
    )
    nahrada = models.ForeignKey(
        "Heslar", models.DO_NOTHING, db_column="nahrada", blank=True, null=True
    )
    pocet_variant_originalu = models.IntegerField(blank=True, null=True)
    odkaz = models.TextField(blank=True, null=True)
    format = models.ForeignKey(
        "Heslar", models.DO_NOTHING, db_column="format", blank=True, null=True
    )
    meritko = models.TextField(blank=True, null=True)
    vyska = models.IntegerField(blank=True, null=True)
    sirka = models.IntegerField(blank=True, null=True)
    cislo_objektu = models.TextField(blank=True, null=True)
    zeme = models.ForeignKey(
        "Heslar", models.DO_NOTHING, db_column="zeme", blank=True, null=True
    )
    region = models.TextField(blank=True, null=True)
    udalost = models.TextField(blank=True, null=True)
    udalost_typ = models.ForeignKey(
        "Heslar", models.DO_NOTHING, db_column="udalost_typ", blank=True, null=True
    )
    rok_od = models.IntegerField(blank=True, null=True)
    rok_do = models.IntegerField(blank=True, null=True)
    duveryhodnost = models.IntegerField(blank=True, null=True)
    geom = models.GeometryField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "dokument_extra_data"


class DokumentJazyk(models.Model):
    dokument = models.OneToOneField(
        Dokument, models.DO_NOTHING, db_column="dokument", primary_key=True
    )
    jazyk = models.ForeignKey("Heslar", models.DO_NOTHING, db_column="jazyk")

    class Meta:
        managed = False
        db_table = "dokument_jazyk"
        unique_together = (("dokument", "jazyk"),)


class DokumentOsoba(models.Model):
    dokument = models.OneToOneField(
        Dokument, models.DO_NOTHING, db_column="dokument", primary_key=True
    )
    osoba = models.ForeignKey("Osoba", models.DO_NOTHING, db_column="osoba")

    class Meta:
        managed = False
        db_table = "dokument_osoba"
        unique_together = (("dokument", "osoba"),)


class DokumentPosudek(models.Model):
    dokument = models.OneToOneField(
        Dokument, models.DO_NOTHING, db_column="dokument", primary_key=True
    )
    posudek = models.ForeignKey("Heslar", models.DO_NOTHING, db_column="posudek")

    class Meta:
        managed = False
        db_table = "dokument_posudek"
        unique_together = (("dokument", "posudek"),)


class DokumentacniJednotka(models.Model):
    typ = models.ForeignKey("Heslar", models.DO_NOTHING, db_column="typ")
    nazev = models.TextField(blank=True, null=True)
    negativni_jednotka = models.BooleanField()
    ident_cely = models.TextField(unique=True, blank=True, null=True)
    pian = models.ForeignKey(
        "Pian", models.DO_NOTHING, db_column="pian", blank=True, null=True
    )
    komponenty = models.ForeignKey(
        "KomponentaVazby",
        models.DO_NOTHING,
        db_column="komponenty",
        blank=True,
        null=True,
    )
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam, models.DO_NOTHING, db_column="archeologicky_zaznam"
    )

    class Meta:
        managed = False
        db_table = "dokumentacni_jednotka"


class ExterniOdkaz(models.Model):
    externi_zdroj = models.ForeignKey(
        "ExterniZdroj",
        models.DO_NOTHING,
        db_column="externi_zdroj",
        blank=True,
        null=True,
    )
    paginace = models.TextField(blank=True, null=True)
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam,
        models.DO_NOTHING,
        db_column="archeologicky_zaznam",
        blank=True,
        null=True,
    )

    class Meta:
        managed = False
        db_table = "externi_odkaz"


class ExterniZdroj(models.Model):
    sysno = models.TextField(blank=True, null=True)
    typ = models.ForeignKey("Heslar", models.DO_NOTHING, db_column="typ")
    nazev = models.TextField(blank=True, null=True)
    edice_rada = models.TextField(blank=True, null=True)
    sbornik_nazev = models.TextField(blank=True, null=True)
    casopis_denik_nazev = models.TextField(blank=True, null=True)
    casopis_rocnik = models.TextField(blank=True, null=True)
    misto = models.TextField(blank=True, null=True)
    vydavatel = models.TextField(blank=True, null=True)
    typ_dokumentu = models.ForeignKey(
        "Heslar", models.DO_NOTHING, db_column="typ_dokumentu", blank=True, null=True
    )
    organizace = models.TextField(blank=True, null=True)
    rok_vydani_vzniku = models.TextField(blank=True, null=True)
    paginace_titulu = models.TextField(blank=True, null=True)
    isbn = models.TextField(blank=True, null=True)
    issn = models.TextField(blank=True, null=True)
    link = models.TextField(blank=True, null=True)
    datum_rd = models.TextField(blank=True, null=True)
    stav = models.SmallIntegerField()
    poznamka = models.TextField(blank=True, null=True)
    ident_cely = models.TextField(unique=True, blank=True, null=True)
    final_cj = models.BooleanField()
    historie = models.ForeignKey(
        "HistorieVazby", models.DO_NOTHING, db_column="historie", blank=True, null=True
    )

    class Meta:
        managed = False
        db_table = "externi_zdroj"


class ExterniZdrojAutor(models.Model):
    externi_zdroj = models.OneToOneField(
        ExterniZdroj, models.DO_NOTHING, db_column="externi_zdroj", primary_key=True
    )
    autor = models.ForeignKey("Osoba", models.DO_NOTHING, db_column="autor")
    poradi = models.IntegerField()

    class Meta:
        managed = False
        db_table = "externi_zdroj_autor"
        unique_together = (("externi_zdroj", "autor"),)


class ExterniZdrojEditor(models.Model):
    externi_zdroj = models.OneToOneField(
        ExterniZdroj, models.DO_NOTHING, db_column="externi_zdroj", primary_key=True
    )
    editor = models.ForeignKey("Osoba", models.DO_NOTHING, db_column="editor")
    poradi = models.IntegerField()

    class Meta:
        managed = False
        db_table = "externi_zdroj_editor"
        unique_together = (
            ("externi_zdroj", "editor"),
            ("poradi", "externi_zdroj"),
        )


class Heslar(models.Model):
    ident_cely = models.TextField(unique=True, blank=True, null=True)
    nazev_heslare = models.ForeignKey(
        "HeslarNazev", models.DO_NOTHING, db_column="nazev_heslare"
    )
    heslo = models.TextField(blank=True, null=True)
    popis = models.TextField(blank=True, null=True)
    zkratka = models.TextField(blank=True, null=True)
    heslo_en = models.TextField()
    popis_en = models.TextField(blank=True, null=True)
    zkratka_en = models.TextField(blank=True, null=True)
    razeni = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "heslar"
        unique_together = (
            ("nazev_heslare", "zkratka"),
            ("nazev_heslare", "zkratka_en"),
        )


class HeslarDatace(models.Model):
    obdobi = models.OneToOneField(
        Heslar, models.DO_NOTHING, db_column="obdobi", primary_key=True
    )
    rok_od_min = models.IntegerField()
    rok_od_max = models.IntegerField()
    rok_do_min = models.IntegerField()
    rok_do_max = models.IntegerField()
    region = models.OneToOneField(
        Heslar, models.DO_NOTHING, db_column="region", blank=True, null=True
    )

    class Meta:
        managed = False
        db_table = "heslar_datace"


class HeslarDokumentTypMaterialRada(models.Model):
    dokument_rada = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="dokument_rada"
    )
    dokument_typ = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="dokument_typ"
    )
    dokument_material = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="dokument_material"
    )
    validated = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = "heslar_dokument_typ_material_rada"
        unique_together = (
            ("dokument_rada", "dokument_typ", "dokument_material"),
            ("dokument_typ", "dokument_material"),
        )


class HeslarHierarchie(models.Model):
    heslo_podrazene = models.OneToOneField(
        Heslar, models.DO_NOTHING, db_column="heslo_podrazene", primary_key=True
    )
    heslo_nadrazene = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="heslo_nadrazene"
    )
    typ = models.TextField()

    class Meta:
        managed = False
        db_table = "heslar_hierarchie"
        unique_together = (("heslo_podrazene", "heslo_nadrazene", "typ"),)


class HeslarNazev(models.Model):
    nazev = models.TextField(unique=True)
    povolit_zmeny = models.BooleanField()

    class Meta:
        managed = False
        db_table = "heslar_nazev"


class HeslarOdkaz(models.Model):
    heslo = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="heslo")
    zdroj = models.TextField()
    nazev_kodu = models.TextField()
    kod = models.TextField()
    uri = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "heslar_odkaz"


class Historie(models.Model):
    datum_zmeny = models.DateTimeField()
    typ_zmeny_old = models.IntegerField(blank=True, null=True)
    uzivatel = models.ForeignKey(AuthUser, models.DO_NOTHING, db_column="uzivatel")
    poznamka = models.TextField(blank=True, null=True)
    vazba = models.ForeignKey("HistorieVazby", models.DO_NOTHING, db_column="vazba")
    typ_zmeny = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "historie"


class HistorieVazby(models.Model):
    typ_vazby = models.TextField()

    class Meta:
        managed = False
        db_table = "historie_vazby"


class Kladysm5(models.Model):
    gid = models.IntegerField(primary_key=True)
    id = models.DecimalField(max_digits=65535, decimal_places=65535)
    mapname = models.TextField()
    mapno = models.TextField()
    podil = models.DecimalField(max_digits=65535, decimal_places=65535)
    geom = models.GeometryField(srid=0)
    cislo = models.TextField()

    class Meta:
        managed = False
        db_table = "kladysm5"


class Kladyzm(models.Model):
    gid = models.AutoField(primary_key=True)
    objectid = models.IntegerField(unique=True)
    kategorie = models.IntegerField()
    cislo = models.CharField(unique=True, max_length=8)
    nazev = models.CharField(max_length=100)
    natoceni = models.DecimalField(max_digits=65535, decimal_places=65535)
    shape_leng = models.DecimalField(max_digits=65535, decimal_places=65535)
    shape_area = models.DecimalField(max_digits=65535, decimal_places=65535)
    the_geom = models.GeometryField(srid=4326)

    class Meta:
        managed = False
        db_table = "kladyzm"


class Komponenta(models.Model):
    obdobi = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="obdobi", blank=True, null=True
    )
    presna_datace = models.TextField(blank=True, null=True)
    areal = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="areal", blank=True, null=True
    )
    poznamka = models.TextField(blank=True, null=True)
    jistota = models.CharField(max_length=1, blank=True, null=True)
    ident_cely = models.TextField(unique=True)
    vazba = models.ForeignKey(
        "KomponentaVazby", models.DO_NOTHING, db_column="vazba", blank=True, null=True
    )

    class Meta:
        managed = False
        db_table = "komponenta"


class KomponentaAktivita(models.Model):
    komponenta = models.OneToOneField(
        Komponenta, models.DO_NOTHING, db_column="komponenta", primary_key=True
    )
    aktivita = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="aktivita")

    class Meta:
        managed = False
        db_table = "komponenta_aktivita"
        unique_together = (("komponenta", "aktivita"),)


class KomponentaVazby(models.Model):
    typ_vazby = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "komponenta_vazby"


class Let(models.Model):
    uzivatelske_oznaceni = models.TextField(blank=True, null=True)
    datum = models.DateTimeField(blank=True, null=True)
    pilot = models.TextField(blank=True, null=True)
    pozorovatel = models.ForeignKey(
        "Osoba", models.DO_NOTHING, db_column="pozorovatel", blank=True, null=True
    )
    ucel_letu = models.TextField(blank=True, null=True)
    typ_letounu = models.TextField(blank=True, null=True)
    letiste_start = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="letiste_start", blank=True, null=True
    )
    letiste_cil = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="letiste_cil", blank=True, null=True
    )
    hodina_zacatek = models.TextField(blank=True, null=True)
    hodina_konec = models.TextField(blank=True, null=True)
    pocasi = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="pocasi", blank=True, null=True
    )
    dohlednost = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="dohlednost", blank=True, null=True
    )
    fotoaparat = models.TextField(blank=True, null=True)
    organizace = models.ForeignKey(
        "Organizace", models.DO_NOTHING, db_column="organizace", blank=True, null=True
    )
    ident_cely = models.TextField(unique=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "let"


class Lokalita(models.Model):
    druh = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="druh")
    popis = models.TextField(blank=True, null=True)
    nazev = models.TextField()
    typ_lokality = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="typ_lokality"
    )
    poznamka = models.TextField(blank=True, null=True)
    final_cj = models.BooleanField()
    zachovalost = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="zachovalost", blank=True, null=True
    )
    jistota = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="jistota", blank=True, null=True
    )
    archeologicky_zaznam = models.OneToOneField(
        ArcheologickyZaznam,
        models.DO_NOTHING,
        db_column="archeologicky_zaznam",
        primary_key=True,
    )

    class Meta:
        managed = False
        db_table = "lokalita"


class Nalez(models.Model):
    komponenta = models.ForeignKey(
        Komponenta, models.DO_NOTHING, db_column="komponenta"
    )
    druh_nalezu = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="druh_nalezu")
    specifikace = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="specifikace", blank=True, null=True
    )
    pocet = models.TextField(blank=True, null=True)
    poznamka = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "nalez"


class NeidentAkce(models.Model):
    katastr = models.ForeignKey(
        "RuianKatastr", models.DO_NOTHING, db_column="katastr", blank=True, null=True
    )
    lokalizace = models.TextField(blank=True, null=True)
    rok_zahajeni = models.IntegerField(blank=True, null=True)
    rok_ukonceni = models.IntegerField(blank=True, null=True)
    pian = models.TextField(blank=True, null=True)
    popis = models.TextField(blank=True, null=True)
    poznamka = models.TextField(blank=True, null=True)
    ident_cely = models.TextField(unique=True)
    dokument_cast = models.OneToOneField(
        DokumentCast,
        models.DO_NOTHING,
        db_column="dokument_cast",
        blank=True,
        null=True,
    )

    class Meta:
        managed = False
        db_table = "neident_akce"


class NeidentAkceVedouci(models.Model):
    neident_akce = models.OneToOneField(
        NeidentAkce, models.DO_NOTHING, db_column="neident_akce", primary_key=True
    )
    vedouci = models.ForeignKey("Osoba", models.DO_NOTHING, db_column="vedouci")

    class Meta:
        managed = False
        db_table = "neident_akce_vedouci"
        unique_together = (("neident_akce", "vedouci"),)


class Notifikace(models.Model):
    id = models.IntegerField(primary_key=True)
    nazev = models.TextField(unique=True)
    popis = models.TextField()

    class Meta:
        managed = False
        db_table = "notifikace"


class NotifikaceProjekt(models.Model):
    uzivatel = models.ForeignKey(AuthUser, models.DO_NOTHING, db_column="uzivatel")
    katastr = models.ForeignKey("RuianKatastr", models.DO_NOTHING, db_column="katastr")

    class Meta:
        managed = False
        db_table = "notifikace_projekt"
        unique_together = (("uzivatel", "katastr"),)


class Organizace(models.Model):
    nazev = models.TextField()
    nazev_zkraceny = models.TextField()
    typ_organizace = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="typ_organizace"
    )
    oao = models.BooleanField()
    mesicu_do_zverejneni = models.IntegerField()
    zverejneni_pristupnost = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="zverejneni_pristupnost"
    )
    nazev_zkraceny_en = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    telefon = models.TextField(blank=True, null=True)
    adresa = models.TextField(blank=True, null=True)
    ico = models.TextField(blank=True, null=True)
    soucast = models.ForeignKey(
        "self", models.DO_NOTHING, db_column="soucast", blank=True, null=True
    )
    nazev_en = models.TextField(blank=True, null=True)
    zanikla = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "organizace"


class Osoba(models.Model):
    jmeno = models.TextField()
    prijmeni = models.TextField()
    vypis = models.TextField()
    vypis_cely = models.TextField()
    rok_narozeni = models.IntegerField(blank=True, null=True)
    rok_umrti = models.IntegerField(blank=True, null=True)
    rodne_prijmeni = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "osoba"


class Oznamovatel(models.Model):
    email = models.TextField()
    adresa = models.TextField()
    odpovedna_osoba = models.TextField()
    oznamovatel = models.TextField()
    telefon = models.TextField()

    class Meta:
        managed = False
        db_table = "oznamovatel"


class Pian(models.Model):
    presnost = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="presnost")
    typ = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="typ")
    geom = models.GeometryField(srid=0)
    geom_sjtsk = models.GeometryField(blank=True, null=True, srid=5514)
    geom_system = models.TextField(
        blank=False, null=False, max_length=6, default="wgs84"
    )
    buffer = models.GeometryField(srid=0)
    zm10 = models.ForeignKey(Kladyzm, models.DO_NOTHING, db_column="zm10")
    zm50 = models.ForeignKey(Kladyzm, models.DO_NOTHING, db_column="zm50")
    ident_cely = models.TextField(unique=True)
    historie = models.ForeignKey(
        HistorieVazby, models.DO_NOTHING, db_column="historie", blank=True, null=True
    )
    stav = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = "pian"


class PianSekvence(models.Model):
    kladyzm = models.ForeignKey(Kladyzm, models.DO_NOTHING)
    sekvence = models.IntegerField()
    katastr = models.BooleanField()

    class Meta:
        managed = False
        db_table = "pian_sekvence"


class Projekt(models.Model):
    stav = models.SmallIntegerField()
    typ_projektu = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="typ_projektu"
    )
    lokalizace = models.TextField(blank=True, null=True)
    kulturni_pamatka_cislo = models.TextField(blank=True, null=True)
    kulturni_pamatka_popis = models.TextField(blank=True, null=True)
    parcelni_cislo = models.TextField(blank=True, null=True)
    podnet = models.TextField(blank=True, null=True)
    uzivatelske_oznaceni = models.TextField(blank=True, null=True)
    vedouci_projektu = models.ForeignKey(
        Osoba, models.DO_NOTHING, db_column="vedouci_projektu", blank=True, null=True
    )
    datum_zahajeni = models.DateField(blank=True, null=True)
    datum_ukonceni = models.DateField(blank=True, null=True)
    planovane_zahajeni_text = models.TextField(blank=True, null=True)
    kulturni_pamatka = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="kulturni_pamatka", blank=True, null=True
    )
    termin_odevzdani_nz = models.DateField(blank=True, null=True)
    ident_cely = models.TextField(unique=True, blank=True, null=True)
    geom = models.GeometryField(srid=0, blank=True, null=True)
    soubory = models.ForeignKey(
        "SouborVazby", models.DO_NOTHING, db_column="soubory", blank=True, null=True
    )
    historie = models.ForeignKey(
        HistorieVazby, models.DO_NOTHING, db_column="historie", blank=True, null=True
    )
    organizace = models.ForeignKey(
        Organizace, models.DO_NOTHING, db_column="organizace", blank=True, null=True
    )
    oznaceni_stavby = models.TextField(blank=True, null=True)
    oznamovatel = models.ForeignKey(
        Oznamovatel, models.DO_NOTHING, db_column="oznamovatel", blank=True, null=True
    )
    planovane_zahajeni = models.TextField(
        blank=True, null=True
    )  # This field type is a guess.

    class Meta:
        managed = False
        db_table = "projekt"
        unique_together = (("id", "oznamovatel"),)


class ProjektKatastr(models.Model):
    projekt = models.OneToOneField(Projekt, models.DO_NOTHING, primary_key=True)
    katastr = models.ForeignKey("RuianKatastr", models.DO_NOTHING)
    hlavni = models.BooleanField()
    id = models.AutoField()

    class Meta:
        managed = False
        db_table = "projekt_katastr"
        unique_together = (("projekt", "katastr"),)


class ProjektOznameniSuffix(models.Model):
    project = models.OneToOneField(Projekt, models.DO_NOTHING)
    last_suffix = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "projekt_oznameni_suffix"


class RuianKatastr(models.Model):
    okres = models.ForeignKey("RuianOkres", models.DO_NOTHING, db_column="okres")
    aktualni = models.BooleanField()
    nazev = models.TextField()
    kod = models.IntegerField()
    definicni_bod = models.GeometryField(srid=0)
    nazev_stary = models.TextField(blank=True, null=True)
    poznamka = models.TextField(blank=True, null=True)
    pian = models.ForeignKey(Pian, models.DO_NOTHING, db_column="pian")
    soucasny = models.ForeignKey(
        "self", models.DO_NOTHING, db_column="soucasny", blank=True, null=True
    )
    hranice = models.GeometryField(srid=0, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "ruian_katastr"


class RuianKraj(models.Model):
    nazev = models.TextField(unique=True)
    kod = models.IntegerField(unique=True)
    rada_id = models.CharField(max_length=1)
    definicni_bod = models.GeometryField(srid=0, blank=True, null=True)
    hranice = models.GeometryField(srid=0, blank=True, null=True)
    aktualni = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "ruian_kraj"


class RuianOkres(models.Model):
    nazev = models.TextField()
    kraj = models.ForeignKey(RuianKraj, models.DO_NOTHING, db_column="kraj")
    spz = models.CharField(max_length=3)
    kod = models.IntegerField()
    nazev_en = models.TextField(blank=True, null=True)
    hranice = models.GeometryField(srid=0, blank=True, null=True)
    definicni_bod = models.GeometryField(srid=0, blank=True, null=True)
    aktualni = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "ruian_okres"


class SamostatnyNalez(models.Model):
    id = models.IntegerField(primary_key=True)
    evidencni_cislo = models.TextField(blank=True, null=True)
    projekt = models.ForeignKey(Projekt, models.DO_NOTHING, db_column="projekt")
    katastr = models.ForeignKey(
        RuianKatastr, models.DO_NOTHING, db_column="katastr", blank=True, null=True
    )
    lokalizace = models.TextField(blank=True, null=True)
    hloubka = models.IntegerField(blank=True, null=True)
    okolnosti = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="okolnosti", blank=True, null=True
    )
    geom = models.GeometryField(srid=0, blank=True, null=True)
    geom_sjtsk = models.GeometryField(srid=0, blank=True, null=True)
    geom_system = models.TextField(
        blank=False, null=False, max_length=6, default="wgs84"
    )
    pristupnost = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="pristupnost")
    obdobi = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="obdobi", blank=True, null=True
    )
    presna_datace = models.TextField(blank=True, null=True)
    druh_nalezu = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="druh_nalezu", blank=True, null=True
    )
    specifikace = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="specifikace", blank=True, null=True
    )
    poznamka = models.TextField(blank=True, null=True)
    nalezce = models.ForeignKey(
        Osoba, models.DO_NOTHING, db_column="nalezce", blank=True, null=True
    )
    datum_nalezu = models.DateField(blank=True, null=True)
    stav = models.SmallIntegerField()
    predano = models.BooleanField(blank=True, null=True)
    predano_organizace = models.ForeignKey(
        Organizace,
        models.DO_NOTHING,
        db_column="predano_organizace",
        blank=True,
        null=True,
    )
    ident_cely = models.TextField(unique=True, blank=True, null=True)
    pocet = models.TextField(blank=True, null=True)
    soubory = models.ForeignKey(
        "SouborVazby", models.DO_NOTHING, db_column="soubory", blank=True, null=True
    )
    historie = models.ForeignKey(
        HistorieVazby, models.DO_NOTHING, db_column="historie", blank=True, null=True
    )

    class Meta:
        managed = False
        db_table = "samostatny_nalez"


class Soubor(models.Model):
    nazev_zkraceny = models.TextField()
    nazev_puvodni = models.TextField()
    rozsah = models.IntegerField(blank=True, null=True)
    vlastnik = models.ForeignKey(AuthUser, models.DO_NOTHING, db_column="vlastnik")
    nazev = models.TextField(unique=True)
    mimetype = models.TextField()
    size_bytes = models.IntegerField()
    vytvoreno = models.DateField()
    vazba = models.ForeignKey("SouborVazby", models.DO_NOTHING, db_column="vazba")
    path = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "soubor"


class SouborDocasny(models.Model):
    ftp_ucet = models.TextField(blank=True, null=True)
    nazev = models.TextField(blank=True, null=True)
    rozsah = models.IntegerField(blank=True, null=True)
    typ_souboru = models.TextField(blank=True, null=True)
    vazba = models.ForeignKey(
        "SouborVazby", models.DO_NOTHING, db_column="vazba", blank=True, null=True
    )

    class Meta:
        managed = False
        db_table = "soubor_docasny"


class SouborVazby(models.Model):
    typ_vazby = models.TextField()

    class Meta:
        managed = False
        db_table = "soubor_vazby"


class StatsLogin(models.Model):
    uzivatel = models.ForeignKey(AuthUser, models.DO_NOTHING, db_column="uzivatel")
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "stats_login"


class SystemovePromenne(models.Model):
    klic = models.CharField(primary_key=True, max_length=200)
    hodnota = models.TextField()

    class Meta:
        managed = False
        db_table = "systemove_promenne"


class Tvar(models.Model):
    dokument = models.ForeignKey(Dokument, models.DO_NOTHING, db_column="dokument")
    tvar = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="tvar")
    poznamka = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "tvar"
        unique_together = (("dokument", "tvar", "poznamka"),)


class Uzivatel(models.Model):
    jmeno = models.TextField(blank=True, null=True)
    email = models.TextField(unique=True)
    heslo = models.TextField()
    auth_level = models.IntegerField()
    telefon = models.TextField(blank=True, null=True)
    organizace = models.IntegerField()
    prijmeni = models.TextField(blank=True, null=True)
    email_potvrzen = models.TextField(blank=True, null=True)
    notifikace_nalezu = models.BooleanField(blank=True, null=True)
    ident_cely = models.TextField(unique=True, blank=True, null=True)
    jazyk = models.CharField(max_length=15)
    historie = models.ForeignKey(
        HistorieVazby, models.DO_NOTHING, db_column="historie", blank=True, null=True
    )
    osoba = models.ForeignKey(
        Osoba, models.DO_NOTHING, db_column="osoba", blank=True, null=True
    )

    class Meta:
        managed = False
        db_table = "uzivatel"


class UzivatelNotifikace(models.Model):
    uzivatel = models.ForeignKey(AuthUser, models.DO_NOTHING, db_column="uzivatel")
    notifikace = models.ForeignKey(
        Notifikace, models.DO_NOTHING, db_column="notifikace"
    )

    class Meta:
        managed = False
        db_table = "uzivatel_notifikace"
        unique_together = (("uzivatel", "notifikace"),)


class UzivatelSpoluprace(models.Model):
    spolupracovnik = models.ForeignKey(
        AuthUser, models.DO_NOTHING, db_column="spolupracovnik"
    )
    vedouci = models.ForeignKey(AuthUser, models.DO_NOTHING, db_column="vedouci")
    aktivni = models.BooleanField()
    potvrzeno = models.BooleanField()
    historie = models.ForeignKey(
        HistorieVazby, models.DO_NOTHING, db_column="historie", blank=True, null=True
    )

    class Meta:
        managed = False
        db_table = "uzivatel_spoluprace"
        unique_together = (("vedouci", "spolupracovnik"),)


class VyskovyBod(models.Model):
    id = models.AutoField()
    adb = models.ForeignKey(Adb, models.DO_NOTHING, db_column="adb")
    ident_cely = models.TextField(unique=True)
    typ = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="typ")
    geom = models.GeometryField(srid=0, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "vyskovy_bod"
