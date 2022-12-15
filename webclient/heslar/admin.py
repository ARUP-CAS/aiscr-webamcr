from django.contrib import admin

from heslar.models import Heslar, HeslarNazev, HeslarDatace, HeslarDokumentTypMaterialRada, HeslarOdkaz, RuianKraj, \
    RuianOkres, RuianKatastr, HeslarHierarchie
from uzivatel.models import Osoba, Organizace


@admin.register(HeslarNazev)
class HeslarNazevAdmin(admin.ModelAdmin):
    list_display = ("nazev", "povolit_zmeny")
    fields = ("nazev", "povolit_zmeny")
    list_filter = ("povolit_zmeny",)
    search_fields = ("nazev",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Heslar)
class HeslarAdmin(admin.ModelAdmin):
    list_display = ("ident_cely", "nazev_heslare", "heslo", "zkratka", "heslo_en", "zkratka_en", "razeni")
    fields = ("nazev_heslare", "ident_cely", "heslo",
              "popis", "zkratka", "heslo_en", "popis_en", "zkratka_en", "razeni")
    search_fields = ("ident_cely", "nazev_heslare__nazev", "heslo",
                     "popis", "zkratka", "heslo_en", "popis_en", "zkratka_en", "razeni")
    list_filter = ("nazev_heslare",)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if add:
            context['adminform'].form.fields['nazev_heslare'].queryset = HeslarNazev.objects.filter(povolit_zmeny=True)
        return super(HeslarAdmin, self).render_change_form(request, context, add, change, form_url, obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.nazev_heslare and not obj.nazev_heslare.povolit_zmeny:
            return False
        return super().has_change_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.pk is not None:
            return "ident_cely", "nazev_heslare"
        else:
            return "ident_cely",

    def has_delete_permission(self, request, obj=None):
        if obj and obj.nazev_heslare and not obj.nazev_heslare.povolit_zmeny:
            return False
        if obj is not None:
            return not obj.has_connections
        return super().has_delete_permission(request)

@admin.register(HeslarDatace)
class HeslarDataceAdmin(admin.ModelAdmin):
    list_display = ("obdobi", "rok_od_min", "rok_do_min", "rok_od_max", "rok_do_max")
    fields = ("obdobi", "rok_od_min", "rok_do_min", "rok_od_max", "rok_do_max")
    search_fields = ("obdobi", "rok_od_min", "rok_do_min", "rok_od_max", "rok_do_max")
    list_filter = ("obdobi", )


@admin.register(HeslarDokumentTypMaterialRada)
class HeslarDokumentTypMaterialRadaAdmin(admin.ModelAdmin):
    list_display = ("dokument_rada", "dokument_typ", "dokument_material")
    readonly_fields = ("dokument_rada", "dokument_typ", "dokument_material")
    fields = ("dokument_rada", "dokument_typ", "dokument_material")
    search_fields = ("dokument_rada", "dokument_typ", "dokument_material")
    list_filter = ("dokument_rada", "dokument_typ", "dokument_material")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(HeslarOdkaz)
class HeslarOdkazAdmin(admin.ModelAdmin):
    list_display = ("heslo", "zdroj", "nazev_kodu", "kod", "uri")
    fields = ("heslo", "zdroj", "nazev_kodu", "kod", "uri")
    search_fields = ("heslo", "zdroj", "nazev_kodu", "kod", "uri")


@admin.register(HeslarHierarchie)
class HeslarHierarchieAdmin(admin.ModelAdmin):
    list_display = ("heslo_podrazene", "heslo_nadrazene", "typ")
    fields = ("heslo_podrazene", "heslo_nadrazene", "typ")
    search_fields = ("heslo_podrazene", "heslo_nadrazene", "typ")
    list_filter = ("typ", )


@admin.register(Osoba)
class OsobaAdmin(admin.ModelAdmin):
    list_display = ("jmeno", "prijmeni", "ident_cely", "vypis", "rok_narozeni", "rok_umrti", "vypis_cely",
                    "rodne_prijmeni")
    fields = ("jmeno", "prijmeni", "ident_cely", "vypis", "vypis_cely", "rok_narozeni", "rok_umrti",
              "rodne_prijmeni")
    search_fields = ("jmeno", "prijmeni", "ident_cely", "vypis", "vypis_cely", "rok_narozeni", "rok_umrti",
                     "rodne_prijmeni")
    readonly_fields = ("ident_cely", )

    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            return not obj.has_connections
        return super().has_delete_permission(request)


@admin.register(Organizace)
class OrganizaceAdmin(admin.ModelAdmin):
    list_display = ("nazev_zkraceny", "typ_organizace", "ident_cely", "oao", "zanikla", "nazev", "nazev_zkraceny_en",
                    "nazev_en", "soucast", "ico", "adresa", "email", "telefon", "zverejneni_pristupnost",
                    "mesicu_do_zverejneni")
    list_filter = ("oao", "zanikla")
    search_fields = ("nazev", "nazev_zkraceny", "typ_organizace__heslo", "zverejneni_pristupnost__heslo", "ident_cely")
    fields = ("nazev", "nazev_zkraceny", "typ_organizace", "oao", "mesicu_do_zverejneni",
              "zverejneni_pristupnost", "nazev_zkraceny_en", "email", "telefon", "adresa", "ico",
              "nazev_en", "zanikla")
    readonly_fields = ("ident_cely", )

    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            return not obj.has_connections
        return super().has_delete_permission(request)


class HeslarRuianAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(RuianKraj)
class HeslarRuianKrajAdmin(HeslarRuianAdmin):
    list_display = ("nazev", "kod", "rada_id")
    fields = ("nazev", "kod", "rada_id", "definicni_bod")
    search_fields = ("nazev", "kod", "rada_id")


@admin.register(RuianOkres)
class HeslarRuianOkresAdmin(HeslarRuianAdmin):
    list_display = ("nazev", "kraj", "spz", "kod", "nazev_en")
    fields = ("nazev", "kraj", "spz", "kod", "nazev_en")
    search_fields = ("nazev", "kraj", "spz", "kod", "nazev_en")
    list_filter = ("kraj",)


@admin.register(RuianKatastr)
class HeslarRuianKatastrAdmin(HeslarRuianAdmin):
    list_display = ("nazev", "okres", "pian_ident_cely", "kod", "nazev_stary")
    fields = ("aktualni", "nazev", "kod", "nazev_stary", "okres")
    search_fields = ("okres", "aktualni", "nazev", "kod", "nazev_stary")
    list_filter = ("okres", "okres__kraj", "aktualni")


