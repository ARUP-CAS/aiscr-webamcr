import crispy_forms
from dal import autocomplete
from crispy_forms.layout import Div, Layout, HTML
from django.db.models import Q
from django.forms import SelectMultiple
from django.utils.translation import gettext as _
from django_filters import (
    CharFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    DateFromToRangeFilter,
    RangeFilter,
)
from django_filters.widgets import DateRangeWidget

from heslar.hesla import (
    HESLAR_ADB_PODNET,
    HESLAR_ADB_TYP,
    HESLAR_AKCE_TYP,
    HESLAR_AKCE_TYP_KAT,
    HESLAR_AKTIVITA,
    HESLAR_AREAL,
    HESLAR_AREAL_KAT,
    HESLAR_DJ_TYP,
    HESLAR_OBDOBI,
    HESLAR_OBDOBI_KAT,
    HESLAR_OBJEKT_DRUH,
    HESLAR_OBJEKT_DRUH_KAT,
    HESLAR_OBJEKT_SPECIFIKACE,
    HESLAR_OBJEKT_SPECIFIKACE_KAT,
    HESLAR_PIAN_PRESNOST,
    HESLAR_PIAN_TYP,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_DRUH_KAT,
    HESLAR_PREDMET_SPECIFIKACE,
    HESLAR_PRISTUPNOST,
    HESLAR_VYSKOVY_BOD_TYP,
)
from heslar.models import Heslar
from historie.models import Historie
from projekt.filters import KatastrFilter
from core.forms import SelectMultipleSeparator
from .models import Akce
from arch_z.models import ArcheologickyZaznam
from uzivatel.models import Organizace, Osoba, User
from dokument.filters import HistorieFilter
from heslar.views import heslar_12


class ArchZaznamFilter(HistorieFilter, KatastrFilter):
    filter_typ = "arch_z"

    stav = MultipleChoiceFilter(
        choices=ArcheologickyZaznam.STATES,
        field_name="archeologicky_zaznam__stav",
        label=_("archZaznam.filter.stav.label"),
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    ident_cely = CharFilter(
        field_name="archeologicky_zaznam__ident_cely",
        lookup_expr="icontains",
        label=_("archZaznam.filter.identCely.label"),
        distinct=True,
    )

    pristupnost = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST),
        label=_("archZaznam.filter.pristupnost.label"),
        field_name="archeologicky_zaznam__pristupnost",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    # Historie
    historie_typ_zmeny = MultipleChoiceFilter(
        choices=filter(lambda x: x[0].startswith("AZ"), Historie.CHOICES),
        label=_("historie.filter.typZmeny.label"),
        field_name="archeologicky_zaznam__historie__historie__typ_zmeny",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    historie_datum_zmeny_od = DateFromToRangeFilter(
        label=_("historie.filter.datumZmeny.label"),
        field_name="archeologicky_zaznam__historie__historie__datum_zmeny",
        widget=DateRangeWidget(attrs={"type": "date", "max": "2100-12-31"}),
        distinct=True,
    )

    historie_uzivatel = ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        field_name="archeologicky_zaznam__historie__historie__uzivatel",
        label=_("historie.filter.uzivatel.label"),
        widget=autocomplete.ModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete"),
        distinct=True,
    )

    # Dj a Pian
    dj_typ = ModelMultipleChoiceFilter(
        label=_("lokalita.filter.djtyp.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DJ_TYP),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__typ",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    dj_nazev = CharFilter(
        label=_("lokalita.filter.djnazev.label"),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__nazev",
        lookup_expr="icontains",
        distinct=True,
    )

    dj_zjisteni = MultipleChoiceFilter(
        method="filter_has_positive_find",
        label=_("lokalita.filter.djZjisteni.label"),
        choices=[("True", "pozitivní"), ("False", "negativní")],
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    pian_ident_obsahuje = CharFilter(
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__pian__ident_cely",
        lookup_expr="icontains",
        label=_("lokalita.filter.pianIdent.label"),
        distinct=True,
    )

    pian_typ = ModelMultipleChoiceFilter(
        label=_("lokalita.filter.pianTyp.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PIAN_TYP),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__pian__typ",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    pian_presnost = ModelMultipleChoiceFilter(
        label=_("lokalita.filter.pianPresnost.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PIAN_PRESNOST),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__pian__presnost",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    komponenta_obdobi = MultipleChoiceFilter(
        method="filter_obdobi",
        label=_("Období"),
        choices=heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT),
        widget=SelectMultipleSeparator(),
    )

    komponenta_areal = MultipleChoiceFilter(
        method="filter_areal",
        label=_("Areál"),
        choices=heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT),
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    komponenta_jistota = MultipleChoiceFilter(
        label=_("lokalita.filter.komponentaJistota.label"),
        method="filter_komponenta_jistota",
        # field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__jistota",
        choices=[
            ("True", _("lokalita.filter.komponentaJistota.ano.label")),
            ("False", _("lokalita.filter.komponentaJistota.ne.label")),
        ],
        widget=SelectMultipleSeparator(),
        distinct=True,
    )
    komponenta_aktivity = ModelMultipleChoiceFilter(
        label=_("lokalita.filter.komponentaAktivity.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_AKTIVITA),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__komponentaaktivita__aktivita",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )
    komponenta_poznamka = CharFilter(
        label=_("lokalita.filter.komponentaPoznamka.label"),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__poznamka",
        distinct=True,
    )

    predmet_druh = MultipleChoiceFilter(
        method="filter_predmety_druh",
        label=_("Druh předmětu"),
        choices=heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT),
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    predmet_specifikace = ModelMultipleChoiceFilter(
        label=_("lokalita.filter.predmetSpecifikace.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PREDMET_SPECIFIKACE),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__predmety__specifikace",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    predmet_pozn_pocet = CharFilter(
        method="filter_predmet_pozn_pocet",
        label=_("lokalita.filter.predmetPoznamkaPocet.label"),
        distinct=True,
    )

    objekt_druh = MultipleChoiceFilter(
        method="filter_objekty_druh",
        label=_("Druh objektu"),
        choices=heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT),
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    objekt_specifikace = MultipleChoiceFilter(
        method="filter_objekty_specifikace",
        label=_("Specifikace objektu"),
        choices=heslar_12(HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT),
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    objekt_pozn_pocet = CharFilter(
        method="filter_objekt_pozn_pocet",
        label=_("lokalita.filter.objektPoznamkaPocet.label"),
        distinct=True,
    )

    dokument_ident = CharFilter(
        field_name="archeologicky_zaznam__casti_dokumentu__dokument__ident_cely",
        lookup_expr="icontains",
        label=_("lokalita.filter.idDokumentu.label"),
        distinct=True,
    )

    zdroj_ident = CharFilter(
        field_name="archeologicky_zaznam__externi_odkazy__externi_zdroj__ident_cely",
        lookup_expr="icontains",
        label=_("lokalita.filter.idZdroje.label"),
        distinct=True,
    )

    vlastnik = ModelMultipleChoiceFilter(
        queryset=User.objects.select_related("organizace").all(),
        field_name="archeologicky_zaznam__historie__historie__uzivatel",
        label="Vlastník",
        widget=SelectMultipleSeparator(),
    )

    def filtr_katastr(self, queryset, name, value):
        return queryset.filter(
            Q(archeologicky_zaznam__hlavni_katastr__nazev__icontains=value)
            | Q(archeologicky_zaznam__katastry__nazev__icontains=value)
        ).distinct()

    def filtr_katastr_kraj(self, queryset, name, value):
        return queryset.filter(
            Q(archeologicky_zaznam__hlavni_katastr__okres__kraj__in=value)
            | Q(archeologicky_zaznam__katastry__okres__kraj__in=value)
        ).distinct()

    def filtr_katastr_okres(self, queryset, name, value):
        return queryset.filter(
            Q(archeologicky_zaznam__hlavni_katastr__okres__in=value)
            | Q(archeologicky_zaznam__katastry__okres__in=value)
        ).distinct()

    def filter_has_positive_find(self, queryset, name, value):
        if "True" in value and "False" in value:
            return queryset.filter(
                Q(
                    archeologicky_zaznam__dokumentacni_jednotky_akce__negativni_jednotka=False
                )
                | Q(
                    archeologicky_zaznam__dokumentacni_jednotky_akce__negativni_jednotka=True
                )
            ).distinct()
        elif "True" in value:
            return queryset.filter(
                archeologicky_zaznam__dokumentacni_jednotky_akce__negativni_jednotka=False
            ).distinct()
        elif "False" in value:
            return queryset.filter(
                archeologicky_zaznam__dokumentacni_jednotky_akce__negativni_jednotka=True
            ).distinct()

    def filter_komponenta_jistota(self, queryset, name, value):
        if "True" in value and "False" in value:
            return queryset.distinct()
        elif "True" in value:
            return queryset.filter(
                archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__jistota=True
            ).distinct()
        elif "False" in value:
            return queryset.exclude(
                archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__jistota=True
            ).distinct()

    def filter_predmet_pozn_pocet(self, queryset, name, value):
        return queryset.filter(
            Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__predmety__poznamka__icontains=value
            )
            | Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__predmety__pocet__icontains=value
            )
        ).distinct()

    def filter_objekt_pozn_pocet(self, queryset, name, value):
        return queryset.filter(
            Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__objekty__poznamka__icontains=value
            )
            | Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__objekty__pocet__icontains=value
            )
        ).distinct()

    def filter_obdobi(self, queryset, name, value):
        return queryset.filter(
            archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__obdobi__in=value
        ).distinct()

    def filter_areal(self, queryset, name, value):
        return queryset.filter(
            archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__areal__in=value
        ).distinct()

    def filter_predmety_druh(self, queryset, name, value):
        return queryset.filter(
            archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__predmety__druh__in=value
        ).distinct()

    def filter_objekty_druh(self, queryset, name, value):
        return queryset.filter(
            archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__objekty__druh__in=value
        ).distinct()

    def filter_objekty_specifikace(self, queryset, name, value):
        return queryset.filter(
            archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__objekty__specifikace__in=value
        ).distinct()


class AkceFilter(ArchZaznamFilter):

    typ = MultipleChoiceFilter(
        method="filter_akce_typ",
        label=_("Typ"),
        choices=heslar_12(HESLAR_AKCE_TYP, HESLAR_AKCE_TYP_KAT),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )

    organizace = ModelMultipleChoiceFilter(
        queryset=Organizace.objects.all(),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )

    vedouci = MultipleChoiceFilter(
        choices=Osoba.objects.all().values_list("id", "vypis_cely"),
        method="filtr_vedouci",
        label=_("akce.filter.vedouci.label"),
        widget=autocomplete.Select2Multiple(
            url="heslar:osoba-autocomplete-choices",
        ),
        distinct=True,
    )

    zahrnout_projektove = MultipleChoiceFilter(
        choices=[("False", _("Ne")), ("True", _("Ano"))],
        label=_("akce.filter.zahrnoutProjektove.label"),
        method="filtr_zahrnout_projektove",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    datum_zahajeni = DateFromToRangeFilter(
        label=_("akce.filter.datumZahajeni.label"),
        field_name="datum_zahajeni",
        widget=DateRangeWidget(attrs={"type": "date", "max": "2100-12-31"}),
        distinct=True,
    )

    datum_ukonceni = DateFromToRangeFilter(
        label=_("akce.filter.datumUkonceni.label"),
        field_name="datum_ukonceni",
        widget=DateRangeWidget(attrs={"type": "date", "max": "2100-12-31"}),
        distinct=True,
    )

    je_nz = MultipleChoiceFilter(
        choices=[("False", _("Ne")), ("True", _("Ano"))],
        label=_("akce.filter.terenniZjisteni.label"),
        method="filtr_je_nz",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    odlozena_nz = MultipleChoiceFilter(
        choices=[("False", _("Ne")), ("True", _("Ano"))],
        label=_("akce.filter.odlozenaNz.label"),
        method="filtr_odlozena_nz",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    adb_ident_obsahuje = CharFilter(
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__adb__ident_cely",
        lookup_expr="icontains",
        label=_("akce.filter.adbIdent.label"),
        distinct=True,
    )

    adb_typ_sondy = ModelMultipleChoiceFilter(
        label=_("akce.filter.adbTypSondy.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_ADB_TYP),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__adb__typ_sondy",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    adb_podnet = ModelMultipleChoiceFilter(
        label=_("akce.filter.adbPodnet.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_ADB_PODNET),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__adb__podnet",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    adb_popisne_udaje = CharFilter(
        method="filter_adb_popisne_udaje",
        label=_("akce.filter.adbPopisneUdaje.label"),
        distinct=True,
    )

    adb_autori = MultipleChoiceFilter(
        choices=Osoba.objects.all().values_list("id", "vypis_cely"),
        method="filtr_adb_autori",
        label=_("akce.filter.adbAutori.label"),
        widget=autocomplete.Select2Multiple(
            url="heslar:osoba-autocomplete-choices",
        ),
        distinct=True,
    )

    adb_roky = DateFromToRangeFilter(
        label=_("akce.filter.adbRoky.label"),
        method="filter_adb_roky",
        widget=DateRangeWidget(attrs={"type": "date", "max": "2100-12-31"}),
        distinct=True,
    )

    vb_ident_obsahuje = CharFilter(
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__adb__vyskove_body__ident_cely",
        lookup_expr="icontains",
        label=_("akce.filter.vbIdent.label"),
        distinct=True,
    )

    vb_uroven = ModelMultipleChoiceFilter(
        label=_("akce.filter.vbUroven.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_VYSKOVY_BOD_TYP),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__adb__vyskove_body__typ",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    vb_niveleta = RangeFilter(
        label=_("akce.filter.vbNiveleta.label"),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__adb__vyskove_body__niveleta",
        distinct=True,
    )

    def filter_akce_typ(self, queryset, name, value):
        return queryset.filter(
            Q(hlavni_typ__in=value) | Q(vedlejsi_typ__in=value)
        ).distinct()

    def filtr_vedouci(self, queryset, name, value):
        return queryset.filter(
            Q(hlavni_vedouci__in=value) | Q(akcevedouci__vedouci__in=value)
        ).distinct()

    def filter_popisne_udaje(self, queryset, name, value):
        return queryset.filter(
            Q(lokalizace_okolnosti__icontains=value)
            | Q(souhrn_upresneni__icontains=value)
            | Q(ulozeni_nalezu__icontains=value)
            | Q(ulozeni_dokumentace__icontains=value)
            | Q(archeologicky_zaznam__uzivatelske_oznaceni__icontains=value)
        ).distinct()

    def filtr_zahrnout_projektove(self, queryset, name, value):
        if value is None:
            return queryset.exclude(typ=Akce.TYP_AKCE_PROJEKTOVA).distinct()
        if "True" in value:
            return queryset
        elif "False" in value:
            return queryset.exclude(typ=Akce.TYP_AKCE_PROJEKTOVA).distinct()

    def filtr_je_nz(self, queryset, name, value):
        if "True" in value and "False" in value:
            return queryset.filter(Q(je_nz=False) | Q(je_nz=True)).distinct()
        elif "True" in value:
            return queryset.filter(je_nz=True).distinct()
        elif "False" in value:
            return queryset.filter(je_nz=False).distinct()

    def filtr_odlozena_nz(self, queryset, name, value):
        if "True" in value and "False" in value:
            return queryset.filter(
                Q(odlozena_nz=False) | Q(odlozena_nz=True)
            ).distinct()
        elif "True" in value:
            return queryset.filter(odlozena_nz=True).distinct()
        elif "False" in value:
            return queryset.filter(odlozena_nz=False).distinct()

    def filter_adb_popisne_udaje(self, queryset, name, value):
        return queryset.filter(
            Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__adb__uzivatelske_oznaceni_sondy__icontains=value
            )
            | Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__adb__cislo_popisne__icontains=value
            )
            | Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__adb__trat__icontains=value
            )
            | Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__adb__parcelni_cislo__icontains=value
            )
            | Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__adb__poznamka__icontains=value
            )
        ).distinct()

    def filtr_adb_autori(self, queryset, name, value):
        return queryset.filter(
            Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__adb__autor_popisu__in=value
            )
            | Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__adb__autor_revize__in=value
            )
        ).distinct()

    def filter_adb_roky(self, queryset, name, value):
        if value.start and value.stop:
            rng = (
                value.start.year,
                value.stop.year,
            )
        elif value.start and not value.stop:
            rng = (
                value.start.year,
                2100,
            )
        elif value.stop and not value.start:
            rng = (1900, value.stop.year)
        else:
            rng = (1900, 2100)
        return queryset.filter(
            Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__adb__rok_popisu__range=rng
            )
            | Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__adb__rok_revize__range=rng
            )
        ).distinct()

    class Meta:
        model = Akce
        exclude = ("projekt",)

    def __init__(self, *args, **kwargs):
        super(AkceFilter, self).__init__(*args, **kwargs)
        self.helper = AkceFilterFormHelper()

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        if not self.form.cleaned_data["zahrnout_projektove"]:
            queryset = queryset.exclude(typ=Akce.TYP_AKCE_PROJEKTOVA)
        return queryset


class AkceFilterFormHelper(crispy_forms.helper.FormHelper):
    form_method = "GET"
    dj_pian_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"akce.filter.djPian.divider.label")
    }
    history_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"akce.filter.history.divider.label")
    }
    komponenta_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"akce.filter.komponenta.divider.label")
    }
    dok_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"akce.filter.dok.divider.label")
    }
    adb_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"akce.filter.adb.divider.label")
    }
    layout = Layout(
        Div(
            Div(
                Div("ident_cely", css_class="col-sm-2"),
                Div("typ", css_class="col-sm-2"),
                Div("stav", css_class="col-sm-2"),
                Div("organizace", css_class="col-sm-2"),
                Div("vedouci", css_class="col-sm-2"),
                Div("pristupnost", css_class="col-sm-2"),
                Div("katastr", css_class="col-sm-2"),
                Div("okres", css_class="col-sm-2"),
                Div("kraj", css_class="col-sm-2"),
                Div("popisne_udaje", css_class="col-sm-4"),
                Div("zahrnout_projektove", css_class="col-sm-2"),
                Div("datum_zahajeni", css_class="col-sm-4 app-daterangepicker"),
                Div("datum_ukonceni", css_class="col-sm-4 app-daterangepicker"),
                Div("je_nz", css_class="col-sm-2"),
                Div("odlozena_nz", css_class="col-sm-2"),
                css_class="row",
            ),
            Div(
                HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                HTML(history_divider),
                HTML(_('<hr class="mt-0" />')),
                data_toggle="collapse",
                href="#historieCollapse",
                role="button",
                aria_expanded="false",
                aria_controls="historieCollapse",
                css_class="col-sm-12 app-btn-show-more collapsed",
            ),
            Div(
                Div("historie_typ_zmeny", css_class="col-sm-2"),
                Div(
                    "historie_datum_zmeny_od", css_class="col-sm-4 app-daterangepicker"
                ),
                Div("historie_uzivatel", css_class="col-sm-4"),
                id="historieCollapse",
                css_class="collapse row",
            ),
            Div(
                HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                HTML(dj_pian_divider),
                HTML(_('<hr class="mt-0" />')),
                data_toggle="collapse",
                href="#DjPianCollapse",
                role="button",
                aria_expanded="false",
                aria_controls="DjPianCollapse",
                css_class="col-sm-12 app-btn-show-more collapsed",
            ),
            Div(
                Div("dj_typ", css_class="col-sm-2"),
                Div("dj_nazev", css_class="col-sm-2"),
                Div("dj_zjisteni", css_class="col-sm-2"),
                Div("pian_ident_obsahuje", css_class="col-sm-2"),
                Div("pian_typ", css_class="col-sm-2"),
                Div("pian_presnost", css_class="col-sm-2"),
                id="DjPianCollapse",
                css_class="collapse row",
            ),
            Div(
                HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                HTML(komponenta_divider),
                HTML(_('<hr class="mt-0" />')),
                data_toggle="collapse",
                href="#KomponentaCollapse",
                role="button",
                aria_expanded="false",
                aria_controls="KomponentaCollapse",
                css_class="col-sm-12 app-btn-show-more collapsed",
            ),
            Div(
                Div("komponenta_obdobi", css_class="col-sm-2"),
                Div("komponenta_jistota", css_class="col-sm-2"),
                Div("komponenta_areal", css_class="col-sm-2"),
                Div("komponenta_aktivity", css_class="col-sm-2"),
                Div("komponenta_poznamka", css_class="col-sm-4"),
                Div("predmet_druh", css_class="col-sm-2"),
                Div("predmet_specifikace", css_class="col-sm-2"),
                Div("predmet_pozn_pocet", css_class="col-sm-4"),
                Div(css_class="col-sm-4"),
                Div("objekt_druh", css_class="col-sm-2"),
                Div("objekt_specifikace", css_class="col-sm-2"),
                Div("objekt_pozn_pocet", css_class="col-sm-4"),
                id="KomponentaCollapse",
                css_class="collapse row",
            ),
            Div(
                HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                HTML(adb_divider),
                HTML(_('<hr class="mt-0" />')),
                data_toggle="collapse",
                href="#AdbCollapse",
                role="button",
                aria_expanded="false",
                aria_controls="AdbCollapse",
                css_class="col-sm-12 app-btn-show-more collapsed",
            ),
            Div(
                Div("adb_ident_obsahuje", css_class="col-sm-2"),
                Div("adb_typ_sondy", css_class="col-sm-2"),
                Div("adb_podnet", css_class="col-sm-2"),
                Div("adb_popisne_udaje", css_class="col-sm-4"),
                Div(css_class="col-sm-2"),
                Div("adb_autori", css_class="col-sm-2"),
                Div("adb_roky", css_class="col-sm-4 app-daterangepicker"),
                Div(css_class="col-sm-6"),
                Div("vb_ident_obsahuje", css_class="col-sm-2"),
                Div("vb_uroven", css_class="col-sm-2"),
                Div("vb_niveleta", css_class="col-sm-4 app-daterangepicker"),
                id="AdbCollapse",
                css_class="collapse row",
            ),
            Div(
                HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                HTML(dok_divider),
                HTML(_('<hr class="mt-0" />')),
                data_toggle="collapse",
                href="#zaznamyCollapse",
                role="button",
                aria_expanded="false",
                aria_controls="zaznamyCollapse",
                css_class="col-sm-12 app-btn-show-more collapsed",
            ),
            Div(
                Div("dokument_ident", css_class="col-sm-2"),
                Div("zdroj_ident", css_class="col-sm-2"),
                id="zaznamyCollapse",
                css_class="collapse row",
            ),
        ),
    )
    form_tag = False
