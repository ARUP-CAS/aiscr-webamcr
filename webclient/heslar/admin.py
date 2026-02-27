import logging

from django.contrib import admin
from django.http import StreamingHttpResponse
from django_object_actions import DjangoObjectActions, action
from heslar.forms import HeslarHierarchieForm, HeslarOdkazForm, OrganizaceAdminForm, OsobaAdminForm
from heslar.models import (
    Heslar,
    HeslarDatace,
    HeslarDokumentTypMaterialRada,
    HeslarHierarchie,
    HeslarNazev,
    HeslarOdkaz,
    RuianKatastr,
    RuianKraj,
    RuianOkres,
)
from pid.views import WikiDataAutocompleteView
from uzivatel.models import Organizace, Osoba

logger = logging.getLogger(__name__)


class ObjectWithMetadataAdmin(DjangoObjectActions, admin.ModelAdmin):
    """Třída `ObjectWithMetadataAdmin` v modulu `webclient.heslar.admin`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    @action(label="Metadata", description="Download of metadata")
    def metadata(self, request, obj):
        """Funkce `ObjectWithMetadataAdmin.metadata` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        metadata = obj.metadata

        def context_processor(content):
            """Funkce `ObjectWithMetadataAdmin.context_processor` v modulu `webclient.heslar.admin`.
            
            Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
            
            :param content: Vstupní hodnota používaná při zpracování.
            :return: Výsledek odpovídající účelu volání.
            """
            yield content

        response = StreamingHttpResponse(context_processor(metadata), content_type="text/xml")
        response["Content-Disposition"] = 'attachment; filename="metadata.xml"'
        return response

    change_actions = ("metadata",)


class HeslarWithMetadataAdmin(ObjectWithMetadataAdmin):
    """Třída `HeslarWithMetadataAdmin` v modulu `webclient.heslar.admin`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
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
        """Funkce `HeslarNazevAdmin.has_add_permission` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """Funkce `HeslarNazevAdmin.has_delete_permission` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return False

    def has_change_permission(self, request, obj=None):
        """Funkce `HeslarNazevAdmin.has_change_permission` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return False


@admin.register(Heslar)
class HeslarAdmin(HeslarWithMetadataAdmin):
    """
    Admin část pro správu modelu heslař.
    """

    list_display = ("ident_cely", "nazev_heslare", "heslo", "heslo_en", "zkratka", "popis", "popis_en", "razeni")
    fields = ("nazev_heslare", "ident_cely", "heslo", "heslo_en", "zkratka", "popis", "popis_en", "razeni")
    search_fields = ("ident_cely", "heslo", "heslo_en", "zkratka", "popis", "popis_en")
    list_filter = ("nazev_heslare",)

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        """Funkce `HeslarAdmin.render_change_form` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param context: Vstupní hodnota používaná při zpracování.
        :param add: Vstupní hodnota používaná při zpracování.
        :param change: Vstupní hodnota používaná při zpracování.
        :param form_url: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if add:
            context["adminform"].form.fields["nazev_heslare"].queryset = HeslarNazev.objects.filter(povolit_zmeny=True)
        return super(HeslarAdmin, self).render_change_form(request, context, add, change, form_url, obj)

    def has_change_permission(self, request, obj=None):
        """Funkce `HeslarAdmin.has_change_permission` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if obj and obj.nazev_heslare and not obj.nazev_heslare.povolit_zmeny:
            return False
        return super().has_change_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        """Funkce `HeslarAdmin.get_readonly_fields` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if obj is not None and obj.pk is not None:
            return "ident_cely", "nazev_heslare"
        else:
            return ("ident_cely",)

    def has_delete_permission(self, request, obj=None):
        """Funkce `HeslarAdmin.has_delete_permission` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
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

    list_display = ("obdobi_ident_cely", "obdobi", "rok_od_min", "rok_od_max", "rok_do_min", "rok_do_max", "poznamka")
    fields = ("obdobi", "rok_od_min", "rok_od_max", "rok_do_min", "rok_do_max", "poznamka")
    search_fields = ("obdobi__ident_cely", "obdobi__heslo", "poznamka")
    list_filter = ("obdobi",)

    def get_readonly_fields(self, request, obj=None):
        """Funkce `HeslarDataceAdmin.get_readonly_fields` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if obj:  # Znamená to, že jde o úpravu existujícího záznamu.
            return ("obdobi",)
        else:
            return []

    def obdobi_ident_cely(self, obj):
        """Funkce `HeslarDataceAdmin.obdobi_ident_cely` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
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
    search_fields = (
        "dokument_rada__heslo",
        "dokument_typ__heslo",
        "dokument_material__heslo",
        "dokument_rada__ident_cely",
        "dokument_typ__ident_cely",
        "dokument_material__ident_cely",
    )
    list_filter = ("dokument_rada", "dokument_typ", "dokument_material")

    def has_add_permission(self, request, obj=None):
        """Funkce `HeslarDokumentTypMaterialRadaAdmin.has_add_permission` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """Funkce `HeslarDokumentTypMaterialRadaAdmin.has_delete_permission` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return False

    def has_change_permission(self, request, obj=None):
        """Funkce `HeslarDokumentTypMaterialRadaAdmin.has_change_permission` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return False


@admin.register(HeslarOdkaz)
class HeslarOdkazAdmin(admin.ModelAdmin):
    """
    Admin část pro správu modelu heslař odkaz.
    """

    list_display = ("heslo_ident_cely", "heslo", "zdroj", "nazev_kodu", "kod", "uri", "skos_mapping_relation")
    fields = ("heslar_nazev", "heslo", "zdroj", "nazev_kodu", "kod", "uri", "skos_mapping_relation", "scheme_uri")
    search_fields = ("heslo__ident_cely", "heslo__heslo", "zdroj", "nazev_kodu", "kod", "uri")
    list_filter = ("zdroj", "skos_mapping_relation")
    form = HeslarOdkazForm

    def heslo_ident_cely(self, obj):
        """Funkce `HeslarOdkazAdmin.heslo_ident_cely` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return obj.heslo.ident_cely


@admin.register(HeslarHierarchie)
class HeslarHierarchieAdmin(admin.ModelAdmin):
    """
    Admin část pro správu modelu heslař hierarchie.
    """

    list_display = ("heslo_podrazene_ident_cely", "heslo_podrazene", "heslo_nadrazene", "typ")
    fields = ("heslar_nazev_podrazene", "heslo_podrazene", "heslar_nazev_nadrazene", "heslo_nadrazene", "typ")
    search_fields = (
        "heslo_podrazene__ident_cely",
        "heslo_podrazene__heslo",
        "heslo_nadrazene__ident_cely",
        "heslo_nadrazene__heslo",
    )
    list_filter = ("typ",)
    form = HeslarHierarchieForm

    def heslo_podrazene_ident_cely(self, obj):
        """Funkce `HeslarHierarchieAdmin.heslo_podrazene_ident_cely` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return obj.heslo_podrazene.ident_cely


@admin.register(Osoba)
class OsobaAdmin(ObjectWithMetadataAdmin):
    """
    Admin část pro správu modelu osob.
    """

    form = OsobaAdminForm

    list_display = (
        "ident_cely",
        "vypis_cely",
        "vypis",
        "prijmeni",
        "rodne_prijmeni",
        "jmeno",
        "rok_narozeni",
        "rok_umrti",
    )
    fields = (
        "ident_cely",
        "jmeno",
        "prijmeni",
        "rodne_prijmeni",
        "vypis_cely",
        "vypis",
        "rok_narozeni",
        "rok_umrti",
        "orcid",
        "wikidata",
    )
    search_fields = ("ident_cely", "vypis_cely", "vypis", "prijmeni", "rodne_prijmeni", "jmeno", "orcid", "wikidata")
    readonly_fields = ("ident_cely",)

    def __init__(self, *args, **kwargs):
        """Funkce `OsobaAdmin.__init__` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param args: Vstupní hodnota používaná při zpracování.
        :param kwargs: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.wiki_data_available = None
        super().__init__(*args, **kwargs)

    def has_delete_permission(self, request, obj=None):
        """Funkce `OsobaAdmin.has_delete_permission` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if obj is not None:
            return not obj.has_connections
        return super().has_delete_permission(request)

    def get_fields(self, request, obj=None):
        """Funkce `OsobaAdmin.get_fields` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        fields = list(self.fields)
        if self.wiki_data_available is None:
            try:
                WikiDataAutocompleteView.api_call("test")
            except Exception as err:
                logger.warning("heslar.admin.OsobaAdmin.get_fields.wikidata_error", extra={"error": err})
                self.wiki_data_available = False
            else:
                self.wiki_data_available = True
        if not self.wiki_data_available:
            fields.remove("wikidata")
        return tuple(fields)


@admin.register(Organizace)
class OrganizaceAdmin(ObjectWithMetadataAdmin):
    """
    Admin část pro správu modelu organizace.
    """

    form = OrganizaceAdminForm
    list_display = (
        "ident_cely",
        "nazev",
        "nazev_en",
        "nazev_zkraceny",
        "nazev_zkraceny_en",
        "soucast",
        "typ_organizace",
        "oao",
        "zanikla",
        "ico",
        "adresa",
        "email",
        "telefon",
        "zverejneni_pristupnost",
        "mesicu_do_zverejneni",
        "cteni_dokumentu",
    )
    list_filter = ("typ_organizace", "oao", "zanikla", "soucast", "zverejneni_pristupnost", "cteni_dokumentu")
    search_fields = (
        "nazev",
        "nazev_zkraceny",
        "ident_cely",
        "nazev_en",
        "nazev_zkraceny_en",
        "ico",
        "adresa",
        "email",
        "telefon",
        "ror",
        "web",
    )
    fields = (
        "ident_cely",
        "nazev",
        "nazev_en",
        "nazev_zkraceny",
        "nazev_zkraceny_en",
        "typ_organizace",
        "oao",
        "mesicu_do_zverejneni",
        "zverejneni_pristupnost",
        "email",
        "telefon",
        "adresa",
        "ico",
        "soucast",
        "zanikla",
        "cteni_dokumentu",
        "ror",
        "licence",
        "web",
    )
    readonly_fields = ("ident_cely",)

    def has_delete_permission(self, request, obj=None):
        """Funkce `OrganizaceAdmin.has_delete_permission` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if obj is not None:
            return not obj.has_connections
        return super().has_delete_permission(request)


class HeslarRuianAdmin(ObjectWithMetadataAdmin):
    """Třída `HeslarRuianAdmin` v modulu `webclient.heslar.admin`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def has_add_permission(self, request, obj=None):
        """Funkce `HeslarRuianAdmin.has_add_permission` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """Funkce `HeslarRuianAdmin.has_delete_permission` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return False

    def has_change_permission(self, request, obj=None):
        """Funkce `HeslarRuianAdmin.has_change_permission` v modulu `webclient.heslar.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return False


@admin.register(RuianKraj)
class HeslarRuianKrajAdmin(ObjectWithMetadataAdmin):
    """
    Admin část pro správu modelu ruian kraj.
    """

    list_display = ("nazev", "kod", "rada_id", "nazev_en", "email")
    fields = ("nazev", "kod", "rada_id", "definicni_bod", "nazev_en", "email")
    search_fields = ("kod", "rada_id", "nazev_en", "email")
    readonly_fields = ("nazev", "kod", "rada_id", "definicni_bod")


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
