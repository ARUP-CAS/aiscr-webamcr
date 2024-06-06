from django.contrib import admin
from django.http import StreamingHttpResponse

from heslar.models import Heslar, HeslarNazev, HeslarDatace, HeslarDokumentTypMaterialRada, HeslarOdkaz, RuianKraj, \
    RuianOkres, RuianKatastr, HeslarHierarchie
from uzivatel.models import Osoba, Organizace, UserNotificationType
from django_object_actions import DjangoObjectActions, action

from heslar.forms import HeslarHierarchieForm, HeslarOdkazForm


class ObjectWithMetadataAdmin(DjangoObjectActions, admin.ModelAdmin):
    @action(label="Metadata", description="Download of metadata")
    def metadata(self, request, obj):
        metadata = obj.metadata

        def context_processor(content):
            yield content

        response = StreamingHttpResponse(context_processor(metadata), content_type="text/xml")
        response['Content-Disposition'] = 'attachment; filename="metadata.xml"'
        return response

    change_actions = ("metadata",)


class HeslarWithMetadataAdmin(ObjectWithMetadataAdmin):
    pass

@admin.register(HeslarNazev)
class HeslarNazevAdmin(admin.ModelAdmin):
    """
    Admin část pro prohlížení modelu heslař název.
    Práva na změnu jsou zakázaná.
    """
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
class HeslarAdmin(HeslarWithMetadataAdmin):
    """
    Admin část pro správu modelu heslař.
    """
    list_display = ("ident_cely", "nazev_heslare", "heslo", "zkratka", "heslo_en", "razeni")
    fields = ("nazev_heslare", "ident_cely", "heslo",
              "popis", "zkratka", "heslo_en", "popis_en", "razeni")
    search_fields = ("ident_cely", "nazev_heslare__nazev", "heslo",
                     "popis", "zkratka", "heslo_en", "popis_en", "razeni")
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
    """
    Admin část pro správu modelu heslař datace.
    """
    list_display = ("obdobi_ident_cely", "obdobi", "rok_od_min", "rok_do_min", "rok_od_max", "rok_do_max")
    fields = ("obdobi", "rok_od_min", "rok_do_min", "rok_od_max", "rok_do_max", "poznamka")
    search_fields = ("obdobi__ident_cely", "obdobi__heslo", "rok_od_min", "rok_do_min", "rok_od_max", "rok_do_max",
                     "poznamka")
    list_filter = ("obdobi", )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # This means this is an edit
            return ("obdobi", )
        else:
            return []

    def obdobi_ident_cely(self, obj):
        return obj.obdobi.ident_cely


@admin.register(HeslarDokumentTypMaterialRada)
class HeslarDokumentTypMaterialRadaAdmin(admin.ModelAdmin):
    """
    Admin část pro prohlížení modelu heslař dokument typ material.
    Práva na změnu jsou zakázaná.
    """
    list_display = ("dokument_rada", "dokument_typ", "dokument_material")
    readonly_fields = ("dokument_rada", "dokument_typ", "dokument_material")
    fields = ("dokument_rada", "dokument_typ", "dokument_material")
    search_fields = ("dokument_rada__ident_cely", "dokument_typ__ident_cely", "dokument_material__ident_cely")
    list_filter = ("dokument_rada", "dokument_typ", "dokument_material")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(HeslarOdkaz)
class HeslarOdkazAdmin(admin.ModelAdmin):
    """
    Admin část pro správu modelu heslař odkaz.
    """
    list_display = ("heslo_ident_cely", "heslo", "zdroj", "nazev_kodu", "kod", "uri", "skos_mapping_relation")
    fields = ("heslar_nazev","heslo", "zdroj", "nazev_kodu", "kod", "uri", "skos_mapping_relation")
    search_fields = ("heslo__ident_cely", "heslo__heslo", "zdroj", "nazev_kodu", "kod", "uri")
    form = HeslarOdkazForm

    def heslo_ident_cely(self, obj):
        return obj.heslo.ident_cely

@admin.register(HeslarHierarchie)
class HeslarHierarchieAdmin(admin.ModelAdmin):
    """
    Admin část pro správu modelu heslař hierarchie.
    """
    list_display = ("heslo_podrazene_ident_cely", "heslo_podrazene", "heslo_nadrazene", "typ")
    fields = ("heslar_nazev_podrazene","heslo_podrazene", "heslar_nazev_nadrazene","heslo_nadrazene", "typ")
    search_fields = ("heslo_podrazene__ident_cely", "heslo_podrazene__heslo", "heslo_nadrazene__ident_cely",
                     "heslo_nadrazene__heslo", "typ")
    list_filter = ("typ", )
    form = HeslarHierarchieForm

    def heslo_podrazene_ident_cely(self, obj):
        return obj.heslo_podrazene.ident_cely



@admin.register(Osoba)
class OsobaAdmin(ObjectWithMetadataAdmin):
    """
    Admin část pro správu modelu osob.
    """
    list_display = ("ident_cely", "jmeno", "prijmeni", "vypis", "rok_narozeni", "rok_umrti", "vypis_cely",
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
class OrganizaceAdmin(ObjectWithMetadataAdmin):
    """
    Admin část pro správu modelu organizace.
    """
    list_display = ("ident_cely", "nazev_zkraceny", "typ_organizace", "oao", "zanikla", "nazev", "nazev_zkraceny_en",
                    "nazev_en", "soucast", "ico", "adresa", "email", "telefon", "zverejneni_pristupnost",
                    "mesicu_do_zverejneni")
    list_filter = ("oao", "zanikla")
    search_fields = ("nazev", "nazev_zkraceny", "typ_organizace__heslo", "zverejneni_pristupnost__heslo", "ident_cely")
    fields = ("nazev", "nazev_zkraceny", "typ_organizace", "oao", "mesicu_do_zverejneni",
              "zverejneni_pristupnost", "nazev_zkraceny_en", "email", "telefon", "adresa", "ico",
              "nazev_en", "soucast", "zanikla")
    readonly_fields = ("ident_cely", )

    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            return not obj.has_connections
        return super().has_delete_permission(request)


class HeslarRuianAdmin(ObjectWithMetadataAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(RuianKraj)
class HeslarRuianKrajAdmin(HeslarRuianAdmin):
    """
    Admin část pro správu modelu ruian kraj.
    """
    list_display = ("nazev", "kod", "rada_id", "nazev_en")
    fields = ("nazev", "kod", "rada_id", "definicni_bod", "nazev_en")
    search_fields = ("kod", "rada_id", "nazev_en")


@admin.register(RuianOkres)
class HeslarRuianOkresAdmin(HeslarRuianAdmin):
    """
    Admin část pro správu modelu ruian okres.
    """
    list_display = ("nazev", "kraj", "spz", "kod", "nazev_en")
    fields = ("nazev", "kraj", "spz", "kod", "nazev_en")
    search_fields = ("nazev", "kraj__nazev", "spz", "kod", "nazev_en")
    list_filter = ("kraj",)


@admin.register(RuianKatastr)
class HeslarRuianKatastrAdmin(HeslarRuianAdmin):
    """
    Admin část pro správu modelu ruian katastr.
    """
    list_display = ("nazev", "okres", "pian_ident_cely", "kod")
    fields = ("nazev", "kod", "okres")
    search_fields = ("okres__nazev", "nazev", "kod")
    list_filter = ("okres", "okres__kraj")
