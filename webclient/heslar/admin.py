from django import forms
from django.contrib import admin
from heslar.models import Heslar, HeslarNazev, HeslarDatace, HeslarDokumentTypMaterialRada, HeslarOdkaz
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
    list_display = ("ident_cely", "nazev_heslare", "heslo", "zkratka")
    readonly_fields = ("ident_cely", "nazev_heslare")
    fields = ("ident_cely", "nazev_heslare", "heslo",
              "popis", "zkratka", "heslo_en", "popis_en", "zkratka_en", "razeni")
    search_fields = ("ident_cely", "nazev_heslare", "heslo",
                     "popis", "zkratka", "heslo_en", "popis_en", "zkratka_en", "razeni")

    def has_change_permission(self, request, obj=None):
        if obj and obj.nazev_heslare and not obj.nazev_heslare.povolit_zmeny:
            return False
        return True


@admin.register(HeslarDatace)
class HeslarDataceAdmin(admin.ModelAdmin):
    list_display = ("obdobi", "rok_od_min", "rok_od_max", "rok_do_max", "region")
    fields = ("obdobi", "rok_od_min", "rok_od_max", "rok_do_max", "region")
    search_fields = ("obdobi", "rok_od_min", "rok_od_max", "rok_do_max", "region")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(HeslarDokumentTypMaterialRada)
class HeslarDokumentTypMaterialRadaAdmin(admin.ModelAdmin):
    list_display = ("dokument_rada", "dokument_typ", "dokument_material", "validated")
    readonly_fields = ("dokument_rada", "dokument_typ", "dokument_material", "validated")
    fields = ("dokument_rada", "dokument_typ", "dokument_material", "validated")
    search_fields = ("dokument_rada", "dokument_typ", "dokument_material", "validated")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(HeslarOdkaz)
class HeslarOdkazAdmin(admin.ModelAdmin):
    list_display = ("heslo", "zdroj", "nazev_kodu", "kod")
    fields = ("heslo", "zdroj", "nazev_kodu", "kod", "uri")
    search_fields = ("heslo", "zdroj", "nazev_kodu", "kod", "uri")


@admin.register(Osoba, HeslarAdmin)
class OsobaAdmin(admin.ModelAdmin):
    list_display = ("jmeno", "prijmeni", "vypis", "rok_narozeni", "rok_umrti", "rok_umrti")
    fields = ("jmeno", "prijmeni", "vypis", "vypis_cely", "rok_narozeni", "rok_umrti", "rodne_prijmeni")
    search_fields = ("jmeno", "prijmeni", "vypis", "vypis_cely", "rok_narozeni", "rok_umrti", "rodne_prijmeni")

@admin.register(Organizace, HeslarAdmin)
class OrganizaceAdmin(admin.ModelAdmin):
    list_display = ("nazev_zkraceny", "typ_organizace", "oao", "zanikla")
    list_filter = ("oao", "zanikla")
    search_fields = ("nazev", "nazev_zkraceny", "typ_organizace", "zverejneni_pristupnost")
    fields = ("nazev", "nazev_zkraceny", "typ_organizace", "oao", "mesicu_do_zverejneni",
              "zverejneni_pristupnost", "nazev_zkraceny_en", "email", "telefon", "adresa", "ico",
              "nazev_en", "zanikla")