import logging

import crispy_forms
from dal import autocomplete
from crispy_forms.layout import Div, Layout, HTML
from django.db.models import Q
from django.forms import Select, SelectMultiple
from django.utils.translation import gettext as _
from django_filters import (
    CharFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    DateFromToRangeFilter,
)
from django_filters.widgets import DateRangeWidget

from heslar.hesla import (
    HESLAR_AKTIVITA,
    HESLAR_AREAL,
    HESLAR_AREAL_KAT,
    HESLAR_DJ_TYP,
    HESLAR_JISTOTA_URCENI,
    HESLAR_LOKALITA_DRUH,
    HESLAR_LOKALITA_TYP,
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
    HESLAR_STAV_DOCHOVANI,
)
from heslar.models import Heslar
from historie.models import Historie
from projekt.filters import KatastrFilter
from .models import Lokalita
from arch_z.models import ArcheologickyZaznam
from uzivatel.models import User
from dokument.filters import HistorieFilter
from heslar.views import heslar_12

logger = logging.getLogger(__name__)


class LokalitaFilter(HistorieFilter, KatastrFilter):

    filter_typ = "lokalita"

    stav = MultipleChoiceFilter(
        choices=ArcheologickyZaznam.STATES,
        field_name="archeologicky_zaznam__stav",
        label=_("lokalita.filter.stav.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    ident_cely = CharFilter(
        field_name="archeologicky_zaznam__ident_cely",
        lookup_expr="icontains",
        label=_("lokalita.filter.identCely.label"),
        distinct=True,
    )

    typ_lokality = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_LOKALITA_TYP),
        label=_("lokalita.filter.typLokality.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    druh_lokality = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_LOKALITA_DRUH),
        label=_("lokalita.filter.druhLokality.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    zachovalost_lokality = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_STAV_DOCHOVANI),
        label=_("lokalita.filter.zachovalostLokality.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    jistota_lokality = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_JISTOTA_URCENI),
        label=_("lokalita.filter.jistotaLokality.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    pristupnost = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST),
        label=_("lokalita.filter.pristupnostLokality.label"),
        field_name="archeologicky_zaznam__pristupnost",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )
    # Historie
    historie_typ_zmeny = MultipleChoiceFilter(
        choices=filter(lambda x: x[0].startswith("AZ"), Historie.CHOICES),
        label=_("historie.filter.typZmeny.label"),
        field_name="archeologicky_zaznam__historie__historie__typ_zmeny",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
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
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
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
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
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
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    pian_presnost = ModelMultipleChoiceFilter(
        label=_("lokalita.filter.pianPresnost.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PIAN_PRESNOST),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__pian__presnost",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    komponenta_obdobi = MultipleChoiceFilter(
        method="filter_obdobi",
        label=_("Období"),
        choices=heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    komponenta_areal = MultipleChoiceFilter(
        method="filter_areal",
        label=_("Areál"),
        choices=heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    komponenta_datace = CharFilter(
        label=_("lokalita.filter.komponentaDatace.label"),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__presna_datace",
        distinct=True,
    )
    komponenta_aktivity = ModelMultipleChoiceFilter(
        label=_("lokalita.filter.komponentaAktivity.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_AKTIVITA),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__komponentaaktivita__aktivita",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
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
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    predmet_specifikace = ModelMultipleChoiceFilter(
        label=_("lokalita.filter.predmetSpecifikace.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PREDMET_SPECIFIKACE),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__predmety__specifikace",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
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
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    objekt_specifikace = MultipleChoiceFilter(
        method="filter_objekty_specifikace",
        label=_("Specifikace objektu"),
        choices=heslar_12(HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
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
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
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
            Q(harcheologicky_zaznam__hlavni_katastr__okres__in=value)
            | Q(archeologicky_zaznam__katastry__okres__in=value)
        ).distinct()

    def filter_popisne_udaje(self, queryset, name, value):
        return queryset.filter(
            Q(nazev__icontains=value)
            | Q(popis__icontains=value)
            | Q(poznamka__icontains=value)
            | Q(archeologicky_zaznam__uzivatelske_oznaceni__icontains=value)
        ).distinct()

    def filter_has_positive_find(self, queryset, name, value):
        if "True" in value and "False" in value:
            return queryset.distinct()
        elif "True" in value:
            return queryset.filter(
                archeologicky_zaznam__dokumentacni_jednotky_akce__negativni_jednotka=False
            ).distinct()
        elif "False" in value:
            return queryset.exclude(
                archeologicky_zaznam__dokumentacni_jednotky_akce__negativni_jednotka=False
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

    class Meta:
        model = Lokalita
        exclude = (
            "nazev",
            "popis",
            "poznamka",
        )

    def __init__(self, *args, **kwargs):
        super(LokalitaFilter, self).__init__(*args, **kwargs)
        self.helper = LokalitaFilterFormHelper()


class LokalitaFilterFormHelper(crispy_forms.helper.FormHelper):
    form_method = "GET"
    dj_pian_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"lokalita.filter.djPian.divider.label")
    }
    history_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"lokalita.filter.history.divider.label")
    }
    komponenta_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"lokalita.filter.komponenta.divider.label")
    }
    dok_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"lokalita.filter.dok.divider.label")
    }
    layout = Layout(
        Div(
            Div(
                Div("ident_cely", css_class="col-sm-2"),
                Div("typ_lokality", css_class="col-sm-2"),
                Div("druh_lokality", css_class="col-sm-2"),
                Div("zachovalost_lokality", css_class="col-sm-2"),
                Div("jistota_lokality", css_class="col-sm-2"),
                Div("stav", css_class="col-sm-2"),
                Div("katastr", css_class="col-sm-2"),
                Div("okres", css_class="col-sm-2"),
                Div("kraj", css_class="col-sm-2"),
                Div("popisne_udaje", css_class="col-sm-4"),
                Div("pristupnost", css_class="col-sm-2"),
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
                Div("komponenta_datace", css_class="col-sm-2"),
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
