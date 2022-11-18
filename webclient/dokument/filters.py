from functools import reduce
import logging
import operator

import crispy_forms
import django_filters as filters
from dal import autocomplete
from django.db import models
from django_filters.widgets import DateRangeWidget
from crispy_forms.layout import Div, Layout, HTML
from django.forms import SelectMultiple, NumberInput
from django_filters import (
    CharFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    NumberFilter,
    DateFromToRangeFilter,
)
from dokument.models import Dokument, DokumentCast, Tvar
from historie.models import Historie
from django.db.models import Q
from heslar.hesla import (
    HESLAR_AREAL_KAT,
    HESLAR_DOHLEDNOST,
    HESLAR_DOKUMENT_MATERIAL,
    HESLAR_DOKUMENT_NAHRADA,
    HESLAR_DOKUMENT_RADA,
    HESLAR_DOKUMENT_ULOZENI,
    HESLAR_DOKUMENT_ZACHOVALOST,
    HESLAR_JAZYK,
    HESLAR_LETFOTO_TVAR,
    HESLAR_LETISTE,
    HESLAR_OBDOBI,
    HESLAR_OBDOBI_KAT,
    HESLAR_DOKUMENT_TYP,
    HESLAR_DOKUMENT_FORMAT,
    HESLAR_OBJEKT_DRUH_KAT,
    HESLAR_OBJEKT_SPECIFIKACE_KAT,
    HESLAR_POCASI,
    HESLAR_POSUDEK_TYP,
    HESLAR_PREDMET_DRUH_KAT,
    HESLAR_PRISTUPNOST,
    HESLAR_UDALOST_TYP,
    MODEL_3D_DOKUMENT_TYPES,
    HESLAR_ZEME,
    HESLAR_AREAL,
    HESLAR_AKTIVITA,
    HESLAR_OBJEKT_DRUH,
    HESLAR_OBJEKT_SPECIFIKACE,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_SPECIFIKACE,
)
from heslar.models import Heslar, RuianKatastr
from uzivatel.models import Organizace, User, Osoba
from django.utils.translation import gettext as _

from heslar.views import heslar_12
from neidentakce.models import NeidentAkce
from komponenta.models import Komponenta
from nalez.models import NalezObjekt
from core.models import Soubor

logger = logging.getLogger(__name__)


class HistorieFilter(filters.FilterSet):

    filter_typ = None
    # Filters by historie
    historie_typ_zmeny = MultipleChoiceFilter(
        choices=filter(lambda x: x[0].startswith("D"), Historie.CHOICES),
        label=_("historie.filter.typZmeny.label"),
        field_name="archeologicky_zaznam__historie__historie__typ_zmeny",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    historie_datum_zmeny_od = DateFromToRangeFilter(
        label=_("historie.filter.datumZmeny.label"),
        field_name="historie__historie__datum_zmeny",
        widget=DateRangeWidget(attrs={"type": "date", "max": "2100-12-31"}),
        distinct=True,
    )

    historie_uzivatel = ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        field_name="historie__historie__uzivatel",
        label=_("historie.filter.uzivatel.label"),
        widget=autocomplete.ModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete"),
        distinct=True,
    )

    def filter_queryset(self, queryset):
        """
        Filter the queryset with the underlying form's `cleaned_data`. You must
        call `is_valid()` or `errors` before calling this method.
        This method should be overridden if additional filtering needs to be
        applied to the queryset before it is cached.
        """
        zmena = self.form.cleaned_data["historie_typ_zmeny"]
        uzivatel = self.form.cleaned_data["historie_uzivatel"]
        datum = self.form.cleaned_data["historie_datum_zmeny_od"]
        filtered = Historie.objects.all()
        if zmena:
            filtered = filtered.filter(typ_zmeny__in=zmena)
        if uzivatel:
            filtered = filtered.filter(uzivatel__in=uzivatel)
        if datum and datum.start:
            filtered = filtered.filter(datum_zmeny__gte=datum.start)
        if datum and datum.stop:
            filtered = filtered.filter(datum_zmeny__lte=datum.stop)
        if self.filter_typ and self.filter_typ == "arch_z":
            queryset = queryset.filter(
                archeologicky_zaznam__historie__historie__in=filtered
            ).distinct()
        else:
            queryset = queryset.filter(historie__historie__in=filtered).distinct()
        for name, value in self.form.cleaned_data.items():
            queryset = self.filters[name].filter(queryset, value)
            assert isinstance(
                queryset, models.QuerySet
            ), "Expected '%s.%s' to return a QuerySet, but got a %s instead." % (
                type(self).__name__,
                name,
                type(queryset).__name__,
            )
        return queryset


class Model3DFilter(HistorieFilter):

    ident_cely = CharFilter(lookup_expr="icontains", label="ID")

    typ_dokumentu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_TYP).filter(
            id__in=MODEL_3D_DOKUMENT_TYPES
        ),
        label=_("Typ"),
        field_name="typ_dokumentu",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    format = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_FORMAT).filter(
            heslo__startswith="3D"
        ),
        label=_("Formát"),
        field_name="extra_data__format",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    stav = MultipleChoiceFilter(
        choices=Dokument.STATES,
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

    autor = ModelMultipleChoiceFilter(
        label=_("Autor"),
        field_name="autori",
        widget=autocomplete.ModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        queryset=Osoba.objects.all(),
    )

    rok_vzniku_od = NumberFilter(
        field_name="rok_vzniku", label=_("Rok vzniku (od-do)"), lookup_expr="gte"
    )

    rok_vzniku_do = NumberFilter(
        field_name="rok_vzniku", label="&nbsp;", lookup_expr="lte"
    )

    duveryhodnost = NumberFilter(
        field_name="extra_data__duveryhodnost",
        label=_("Důvěryhodnost (min. %)"),
        lookup_expr="gte",
        widget=NumberInput(attrs={"min": "1", "max": "100"}),
        distinct=True,
    )
    popisne_udaje = CharFilter(
        label=_("Popisné údaje"),
        method="filter_popisne_udaje",
    )

    zeme = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_ZEME),
        field_name="extra_data__zeme",
        label=_("Země"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    obdobi = MultipleChoiceFilter(
        method="filter_obdobi",
        label=_("Období"),
        choices=heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)[1:],
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )

    areal = MultipleChoiceFilter(
        method="filter_areal",
        label=_("Areál"),
        choices=heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)[1:],
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    aktivity = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(
            nazev_heslare=HESLAR_AKTIVITA
        ),  # nezda se mi pouziti obou hesel - plati i pro create a edit
        field_name="casti__komponenty__komponenty__komponentaaktivita__aktivita",
        label=_("Aktivity"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    predmet_druh = MultipleChoiceFilter(
        field_name="casti__komponenty__komponenty__predmety__druh",
        label=_("Druh předmětu"),
        choices=heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT)[1:],
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    predmet_specifikace = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(
            nazev_heslare=HESLAR_PREDMET_SPECIFIKACE
        ),  # nezda se mi pouziti obou hesel - plati i pro create a edit
        field_name="casti__komponenty__komponenty__predmety__specifikace",
        label=_("Specifikace předmětu"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )
    objekt_druh = MultipleChoiceFilter(
        field_name="casti__komponenty__komponenty__objekty__druh",
        label=_("Druh objektu"),
        choices=heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT)[1:],
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    objekt_specifikace = MultipleChoiceFilter(
        field_name="casti__komponenty__komponenty__objekty__specifikace",
        label=_("Specifikace objektu"),
        choices=heslar_12(HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT)[1:],
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    def filter_popisne_udaje(self, queryset, name, value):
        return queryset.filter(
            Q(oznaceni_originalu__icontains=value)
            | Q(popis__icontains=value)
            | Q(poznamka__icontains=value)
            | Q(extra_data__odkaz__icontains=value)
            | Q(casti__komponenty__komponenty__objekty__poznamka__icontains=value)
            | Q(casti__komponenty__komponenty__predmety__poznamka__icontains=value)
        )

    def filter_obdobi(self, queryset, name, value):
        return queryset.filter(casti__komponenty__komponenty__obdobi__in=value)

    def filter_areal(self, queryset, name, value):
        return queryset.filter(casti__komponenty__komponenty__areal__in=value)

    class Meta:
        model = Dokument
        exclude = []

    def __init__(self, *args, **kwargs):
        super(Model3DFilter, self).__init__(*args, **kwargs)
        self.helper = Model3DFilterFormHelper()


class Model3DFilterFormHelper(crispy_forms.helper.FormHelper):
    form_method = "GET"
    history_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"dokument.filter.history.divider.label")
    }
    layout = Layout(
        Div(
            Div(
                Div("ident_cely", css_class="col-sm-2"),
                Div("typ_dokumentu", css_class="col-sm-2"),
                Div("format", css_class="col-sm-2"),
                Div("stav", css_class="col-sm-2"),
                Div("organizace", css_class="col-sm-2"),
                Div("autor", css_class="col-sm-2"),
                Div("rok_vzniku_od", css_class="col-sm-2"),
                Div("rok_vzniku_do", css_class="col-sm-2"),
                Div("duveryhodnost", css_class="col-sm-2"),
                Div("popisne_udaje", css_class="col-sm-4"),
                Div("zeme", css_class="col-sm-2"),
                Div("obdobi", css_class="col-sm-2"),
                Div("areal", css_class="col-sm-2"),
                Div("aktivity", css_class="col-sm-2"),
                css_class="row",
            ),
            Div(
                Div("predmet_druh", css_class="col-sm-2"),
                Div("predmet_specifikace", css_class="col-sm-2"),
                Div("objekt_druh", css_class="col-sm-2"),
                Div("objekt_specifikace", css_class="col-sm-2"),
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
        ),
    )
    form_tag = False


class DokumentFilter(Model3DFilter):
    rada = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_RADA),
        label=_("dokument.filter.rada.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    typ_dokumentu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_TYP).exclude(
            id__in=MODEL_3D_DOKUMENT_TYPES
        ),
        label=_("Typ"),
        field_name="typ_dokumentu",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    material_originalu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_MATERIAL),
        label=_("dokument.filter.material.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    uzemni_prislusnost = MultipleChoiceFilter(
        method="filter_uzemni_prislusnost",
        label=_("dokument.filter.uzemniPrislusnost.label"),
        choices=(
            ("M-", _("dokument.filter.uzemniPrislusnost.M.option")),
            ("C-", _("dokument.filter.uzemniPrislusnost.C.option")),
        ),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )
    jazyky = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_JAZYK),
        label=_("dokument.filter.jazyky.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    ulozeni_originalu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_ULOZENI),
        label=_("dokument.filter.ulozeniOriginalu.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    posudky = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_POSUDEK_TYP),
        label=_("dokument.filter.posudky.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    pristupnost = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST),
        label=_("dokument.filter.ulozeniOriginalu.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    datum_zverejneni = DateFromToRangeFilter(
        label=_("dokument.filter.datumZverejneni.label"),
        widget=DateRangeWidget(attrs={"type": "date", "max": "2100-12-31"}),
        distinct=True,
    )
    datum_vzniku = DateFromToRangeFilter(
        label=_("dokument.filter.datumVzniku.label"),
        field_name="extra_data__datum_vzniku",
        widget=DateRangeWidget(attrs={"type": "date", "max": "2100-12-31"}),
        distinct=True,
    )
    zachovalost = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_ZACHOVALOST),
        label=_("dokument.filter.zachovalost.label"),
        field_name="extra_data__zachovalost",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    nahrada = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_NAHRADA),
        label=_("dokument.filter.nahrada.label"),
        field_name="extra_data__nahrada",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    udalost_typ = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_UDALOST_TYP),
        label=_("dokument.filter.udalostTyp.label"),
        field_name="extra_data__udalost_typ",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    rok_udalosti_od = NumberFilter(
        field_name="extra_data__rok_od",
        label=_("dokument.filter.rokUdalosti.label"),
        lookup_expr="gte",
    )

    rok_udalosti_do = NumberFilter(
        field_name="extra_data__rok_do", label="&nbsp;", lookup_expr="lte"
    )
    osoby = ModelMultipleChoiceFilter(
        label=_("dokument.filter.osoby.label"),
        widget=autocomplete.ModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        queryset=Osoba.objects.all(),
    )
    duveryhodnost_od = NumberFilter(
        field_name="extra_data__duveryhodnost",
        label=_("dokument.filter.duveryhodnostOdDo.label"),
        lookup_expr="gte",
    )

    duveryhodnost_do = NumberFilter(
        field_name="extra_data__duveryhodnost", label="&nbsp;", lookup_expr="lte"
    )

    jistota = MultipleChoiceFilter(
        choices=[("True", _("Ano")), ("False", _("Ne"))],
        method="filter_jistota",
        label=_("dokument.filter.jistotaDatace.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    poznamka_komponenty = CharFilter(
        label=_("dokument.filter.poznamkaKomponenty.label"),
        field_name="casti__komponenty__komponenty__poznamka",
        lookup_expr="icontains",
        distinct=True,
    )

    predmet_pozn_pocet = CharFilter(
        method="filter_predmet_pozn_pocet",
        label=_("lokalita.filter.predmetPoznamkaPocet.label"),
        distinct=True,
    )

    objekt_pozn_pocet = CharFilter(
        method="filter_objekt_pozn_pocet",
        label=_("lokalita.filter.objektPoznamkaPocet.label"),
        distinct=True,
    )

    neident_katastr = CharFilter(
        label=_("dokument.filter.neidentAkceKatastr.label"),
        field_name="casti__neident_akce__katastr__nazev",
        distinct=True,
    )

    neident_vedouci = ModelMultipleChoiceFilter(
        label=_("dokument.filter.neidentVedouci.label"),
        field_name="casti__neident_akce__neidentakcevedouci__vedouci",
        widget=autocomplete.ModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        queryset=Osoba.objects.all(),
    )

    neident_rok_zahajeni_od = NumberFilter(
        field_name="casti__neident_akce__rok_zahajeni",
        label=_("dokument.filter.neidentRok.label"),
        lookup_expr="gte",
    )

    neident_rok_ukonceni_do = NumberFilter(
        field_name="casti__neident_akce__rok_ukonceni",
        label="&nbsp;",
        lookup_expr="lte",
    )

    neident_poznamka = CharFilter(
        method="filter_neident_poznamka",
        label=_("dokument.filter.neidentPoznamka.label"),
        distinct=True,
    )

    let_id = CharFilter(
        lookup_expr="icontains",
        label=_("dokument.filter.letId.label"),
        field_name="let__ident_cely",
    )

    let_datum = DateFromToRangeFilter(
        label=_("dokument.filter.letId.label"),
        field_name="let__datum",
        widget=DateRangeWidget(attrs={"type": "date", "max": "2100-12-31"}),
        distinct=True,
    )

    let_pilot = CharFilter(
        lookup_expr="icontains",
        label=_("dokument.filter.letPilot.label"),
        field_name="let__pilot",
    )

    let_pozorovatel = ModelMultipleChoiceFilter(
        label=_("dokument.filter.letPozorovatel.label"),
        field_name="let__pozorovatel",
        widget=autocomplete.ModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        queryset=Osoba.objects.all(),
    )

    let_organizace = ModelMultipleChoiceFilter(
        queryset=Organizace.objects.all(),
        label=_("dokument.filter.letOrganizace.label"),
        field_name="let__organizace",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )

    letiste_start = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_LETISTE),
        label=_("dokument.filter.letLetisteStart.label"),
        field_name="let__letiste_start",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    letiste_cil = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_LETISTE),
        label=_("dokument.filter.letLetisteCil.label"),
        field_name="let__letiste_cil",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    let_pocasi = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_POCASI),
        label=_("dokument.filter.letPocasi.label"),
        field_name="let__pocasi",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    let_dohlednost = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOHLEDNOST),
        label=_("dokument.filter.letDohlednost.label"),
        field_name="let__dohlednost",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    let_poznamka = CharFilter(
        method="filter_let_poznamka",
        label=_("dokument.filter.letPoznamka.label"),
        distinct=True,
    )

    let_ucel = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOHLEDNOST),
        label=_("dokument.filter.letUcel.label"),
        field_name="let__ucel_letu",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    tvary = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_LETFOTO_TVAR),
        label=_("dokument.filter.tvary.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    tvar_poznamka = CharFilter(
        field_name="tvary__poznamka",
        label=_("dokument.filter.tvaryPoznamka.label"),
        distinct=True,
    )
    soubor_velikost_od = NumberFilter(
        method="filter_soubory_velikost_od",
        label=_("dokument.filter.souborVelikost.label"),
    )

    soubor_velikost_do = NumberFilter(
        method="filter_soubory_velikost_do",
        label="&nbsp;",
    )

    soubor_pocet_stran_od = NumberFilter(
        field_name="soubory__soubory__pocet_stran",
        label=_("dokument.filter.souborPocetStran.label"),
        lookup_expr="gte",
    )

    soubor_pocet_stran_do = NumberFilter(
        field_name="soubory__soubory__pocet_stran",
        label="&nbsp;",
        lookup_expr="lte",
    )
    soubor_puvodni_nazev = CharFilter(
        field_name="soubory__soubory__nazev_puvodni",
        label=_("dokument.filter.souborPuvodniNazev.label"),
        distinct=True,
    )
    id_vazby = CharFilter(
        method="filter_id_vazby",
        label=_("dokument.filter.vazbyId.label"),
        distinct=True,
    )

    exist_neident_akce = MultipleChoiceFilter(
        choices=[("True", _("Ano")), ("False", _("Ne"))],
        method="filter_exist_neident_akce",
        label=_("dokument.filter.existNeidentAkce.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    exist_komponenty = MultipleChoiceFilter(
        choices=[("True", _("Ano")), ("False", _("Ne"))],
        method="filter_exist_komponenty",
        label=_("dokument.filter.existKomponenta.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    exist_nalezy = MultipleChoiceFilter(
        choices=[("True", _("Ano")), ("False", _("Ne"))],
        method="filter_exist_nalezy",
        label=_("dokument.filter.existNalezy.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    exist_tvary = MultipleChoiceFilter(
        choices=[("True", _("Ano")), ("False", _("Ne"))],
        method="filter_exist_tvary",
        label=_("dokument.filter.existTvary.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    exist_soubory = MultipleChoiceFilter(
        choices=[("True", _("Ano")), ("False", _("Ne"))],
        method="filter_exist_soubory",
        label=_("dokument.filter.existSoubory.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    def filter_uzemni_prislusnost(self, queryset, name, value):
        logger.debug("Uzemni prislusnost filtering")
        logger.debug(value)
        query = reduce(operator.or_, (Q(ident_cely__contains=item) for item in value))
        return queryset.filter(query)

    def filter_popisne_udaje(self, queryset, name, value):
        return queryset.filter(
            Q(oznaceni_originalu__icontains=value)
            | Q(popis__icontains=value)
            | Q(poznamka__icontains=value)
            | Q(licence__icontains=value)
            | Q(extra_data__cislo_objektu__icontains=value)
            | Q(extra_data__region__icontains=value)
            | Q(extra_data__udalost__icontains=value)
        )

    def filter_predmet_pozn_pocet(self, queryset, name, value):
        return queryset.filter(
            Q(casti__komponenty__komponenty__predmety__poznamka__icontains=value)
            | Q(casti__komponenty__komponenty__predmety__pocet__icontains=value)
        ).distinct()

    def filter_objekt_pozn_pocet(self, queryset, name, value):
        return queryset.filter(
            Q(casti__komponenty__komponenty__objekty__poznamka__icontains=value)
            | Q(casti__komponenty__komponenty__objekty__pocet__icontains=value)
        ).distinct()

    def filter_jistota(self, queryset, name, value):
        if "True" in value and "False" in value:
            return queryset.distinct()
        elif "True" in value:
            return queryset.filter(
                casti__komponenty__komponenty__jistota=True
            ).distinct()
        elif "False" in value:
            return queryset.exclude(
                casti__komponenty__komponenty__jistota=True
            ).distinct()
        else:
            return queryset.distinct()

    def filter_neident_poznamka(self, queryset, name, value):
        return queryset.filter(
            Q(casti__neident_akce__poznamka__icontains=value)
            | Q(casti__neident_akce__popis__icontains=value)
            | Q(casti__neident_akce__pian__icontains=value)
            | Q(casti__neident_akce__lokalizace__icontains=value)
        ).distinct()

    def filter_let_poznamka(self, queryset, name, value):
        return queryset.filter(
            Q(let__typ_letounu__icontains=value)
            | Q(let__fotoaparat__icontains=value)
            | Q(let__uzivatelske_oznaceni__icontains=value)
            | Q(let__ucel_letu__icontains=value)
        ).distinct()

    def filter_soubory_velikost_od(self, queryset, name, value):
        if value:
            value = value * 1024
            return queryset.filter(soubory__soubory__size_bytes__gte=value)
        else:
            return queryset

    def filter_soubory_velikost_do(self, queryset, name, value):
        if value:
            value = value * 1024
            return queryset.filter(soubory__soubory__size_bytes__lte=value)
        else:
            return queryset

    def filter_id_vazby(self, queryset, name, value):
        return queryset.filter(
            Q(casti__archeologicky_zaznam__ident_cely__icontains=value)
            | Q(casti__projekt__ident_cely__icontains=value)
        ).distinct()

    def filter_exist_neident_akce(self, queryset, name, value):
        if len(value) == 1:
            akce = NeidentAkce.objects.filter(dokument_cast=models.OuterRef("pk"))
            if "True" in value:
                casti = DokumentCast.objects.filter(models.Exists(akce))
                return queryset.filter(casti__in=casti).distinct()
            else:
                casti = DokumentCast.objects.filter(models.Exists(akce))
                bez_casti = casti.filter(dokument=models.OuterRef("pk"))
                return queryset.exclude(models.Exists(bez_casti)).distinct()

        else:
            return queryset.distinct()

    def filter_exist_komponenty(self, queryset, name, value):
        if len(value) == 1:
            komponenty = Komponenta.objects.filter(
                komponenta_vazby__casti_dokumentu=models.OuterRef("pk")
            )
            casti = DokumentCast.objects.filter(models.Exists(komponenty))
            if "True" in value:
                return queryset.filter(casti__in=casti).distinct()
            else:
                bez_casti = casti.filter(dokument=models.OuterRef("pk"))
                return queryset.exclude(models.Exists(bez_casti)).distinct()

        else:
            return queryset.distinct()

    def filter_exist_nalezy(self, queryset, name, value):
        if len(value) == 1:
            objekty = NalezObjekt.objects.filter(
                komponenta__komponenta_vazby__casti_dokumentu=models.OuterRef("pk")
            )
            casti_objekty = DokumentCast.objects.filter(models.Exists(objekty))
            predmety = NalezObjekt.objects.filter(
                komponenta__komponenta_vazby__casti_dokumentu=models.OuterRef("pk")
            )
            casti_predmety = DokumentCast.objects.filter(models.Exists(predmety))
            if "True" in value:
                return queryset.filter(
                    Q(casti__in=casti_objekty) | Q(casti__in=casti_predmety)
                ).distinct()
            else:
                bez_casti_objekty = casti_objekty.filter(dokument=models.OuterRef("pk"))
                bez_casti_predmety = casti_predmety.filter(
                    dokument=models.OuterRef("pk")
                )
                return (
                    queryset.exclude(models.Exists(bez_casti_objekty))
                    .exclude(models.Exists(bez_casti_predmety))
                    .distinct()
                )

        else:
            return queryset.distinct()

    def filter_exist_tvary(self, queryset, name, value):
        if len(value) == 1:
            tvar = Tvar.objects.filter(dokument=models.OuterRef("pk"))
            if "True" in value:
                return queryset.filter(models.Exists(tvar)).distinct()
            else:
                return queryset.filter(~models.Exists(tvar)).distinct()

        else:
            return queryset.distinct()

    def filter_exist_soubory(self, queryset, name, value):
        if len(value) == 1:
            soubor = Soubor.objects.filter(
                vazba__dokument_souboru=models.OuterRef("pk")
            )
            if "True" in value:
                return queryset.filter(models.Exists(soubor)).distinct()
            else:
                return queryset.filter(~models.Exists(soubor)).distinct()

        else:
            return queryset.distinct()

    def __init__(self, *args, **kwargs):
        super(DokumentFilter, self).__init__(*args, **kwargs)
        self.helper = DokumentFilterFormHelper()


class DokumentFilterFormHelper(crispy_forms.helper.FormHelper):
    form_method = "GET"
    history_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"dokument.filter.history.divider.label")
    }
    extra_data_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"dokument.filter.extraData.divider.label")
    }
    komponenta_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"dokument.filter.komponentaNalez.divider.label")
    }
    neident_akce_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"dokument.filter.neidentAkce.divider.label")
    }
    lety_tvary_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"dokument.filter.letyTvary.divider.label")
    }
    soubory_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"dokument.filter.soubory.divider.label")
    }
    vazby_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"dokument.filter.vazby.divider.label")
    }
    layout = Layout(
        Div(
            Div(
                Div("ident_cely", css_class="col-sm-2"),
                Div("rada", css_class="col-sm-2"),
                Div("typ_dokumentu", css_class="col-sm-2"),
                Div("material_originalu", css_class="col-sm-2"),
                Div("uzemni_prislusnost", css_class="col-sm-2"),
                Div("stav", css_class="col-sm-2"),
                Div("autor", css_class="col-sm-2"),
                Div("organizace", css_class="col-sm-2"),
                Div("rok_vzniku_od", css_class="col-sm-2"),
                Div("rok_vzniku_do", css_class="col-sm-2"),
                Div("popisne_udaje", css_class="col-sm-4"),
                Div("jazyky", css_class="col-sm-2"),
                Div("ulozeni_originalu", css_class="col-sm-2"),
                Div("posudky", css_class="col-sm-2"),
                Div("pristupnost", css_class="col-sm-2"),
                Div("datum_zverejneni", css_class="col-sm-4 app-daterangepicker"),
                Div("exist_neident_akce", css_class="col-sm-2"),
                Div("exist_komponenty", css_class="col-sm-2"),
                Div("exist_nalezy", css_class="col-sm-2"),
                Div("exist_tvary", css_class="col-sm-2"),
                Div("exist_soubory", css_class="col-sm-2"),
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
                HTML(extra_data_divider),
                HTML(_('<hr class="mt-0" />')),
                data_toggle="collapse",
                href="#extraDataCollapse",
                role="button",
                aria_expanded="false",
                aria_controls="extraDataCollapse",
                css_class="col-sm-12 app-btn-show-more collapsed",
            ),
            Div(
                Div("datum_vzniku", css_class="col-sm-4 app-daterangepicker"),
                Div("zachovalost", css_class="col-sm-2"),
                Div("nahrada", css_class="col-sm-2"),
                Div("format", css_class="col-sm-2"),
                Div("zeme", css_class="col-sm-2"),
                Div("udalost_typ", css_class="col-sm-2"),
                Div("rok_udalosti_od", css_class="col-sm-2"),
                Div("rok_udalosti_do", css_class="col-sm-2"),
                Div("osoby", css_class="col-sm-2"),
                Div("duveryhodnost_od", css_class="col-sm-2"),
                Div("duveryhodnost_do", css_class="col-sm-2"),
                id="extraDataCollapse",
                css_class="collapse row",
            ),
            Div(
                HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                HTML(komponenta_divider),
                HTML(_('<hr class="mt-0" />')),
                data_toggle="collapse",
                href="#komponentaCollapse",
                role="button",
                aria_expanded="false",
                aria_controls="komponentaCollapse",
                css_class="col-sm-12 app-btn-show-more collapsed",
            ),
            Div(
                Div("obdobi", css_class="col-sm-2"),
                Div("jistota", css_class="col-sm-2"),
                Div("areal", css_class="col-sm-2"),
                Div("aktivity", css_class="col-sm-2"),
                Div("poznamka_komponenty", css_class="col-sm-4"),
                Div("predmet_druh", css_class="col-sm-2"),
                Div("predmet_specifikace", css_class="col-sm-2"),
                Div("predmet_pozn_pocet", css_class="col-sm-4"),
                Div(css_class="col-sm-4"),
                Div("objekt_druh", css_class="col-sm-2"),
                Div("objekt_specifikace", css_class="col-sm-2"),
                Div("objekt_pozn_pocet", css_class="col-sm-4"),
                Div(css_class="col-sm-4"),
                id="komponentaCollapse",
                css_class="collapse row",
            ),
            Div(
                HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                HTML(neident_akce_divider),
                HTML(_('<hr class="mt-0" />')),
                data_toggle="collapse",
                href="#neidentAkceCollapse",
                role="button",
                aria_expanded="false",
                aria_controls="neidentAkceCollapse",
                css_class="col-sm-12 app-btn-show-more collapsed",
            ),
            Div(
                Div("neident_katastr", css_class="col-sm-2"),
                Div("neident_vedouci", css_class="col-sm-2"),
                Div("neident_rok_zahajeni_od", css_class="col-sm-2"),
                Div("neident_rok_ukonceni_do", css_class="col-sm-2"),
                Div("neident_poznamka", css_class="col-sm-2"),
                id="neidentAkceCollapse",
                css_class="collapse row",
            ),
            Div(
                HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                HTML(lety_tvary_divider),
                HTML(_('<hr class="mt-0" />')),
                data_toggle="collapse",
                href="#letyTvaryCollapse",
                role="button",
                aria_expanded="false",
                aria_controls="letyTvaryCollapse",
                css_class="col-sm-12 app-btn-show-more collapsed",
            ),
            Div(
                Div("let_id", css_class="col-sm-2"),
                Div("let_datum", css_class="col-sm-4 app-daterangepicker"),
                Div("let_pilot", css_class="col-sm-2"),
                Div("let_pozorovatel", css_class="col-sm-2"),
                Div("let_organizace", css_class="col-sm-2"),
                Div("letiste_start", css_class="col-sm-2"),
                Div("letiste_cil", css_class="col-sm-2"),
                Div("let_pocasi", css_class="col-sm-2"),
                Div("let_dohlednost", css_class="col-sm-2"),
                Div("let_poznamka", css_class="col-sm-4"),
                Div("let_ucel", css_class="col-sm-2"),
                Div(css_class="col-sm-4"),
                Div("tvary", css_class="col-sm-2"),
                Div("tvar_poznamka", css_class="col-sm-4"),
                id="letyTvaryCollapse",
                css_class="collapse row",
            ),
            Div(
                HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                HTML(soubory_divider),
                HTML(_('<hr class="mt-0" />')),
                data_toggle="collapse",
                href="#souboryCollapse",
                role="button",
                aria_expanded="false",
                aria_controls="souboryCollapse",
                css_class="col-sm-12 app-btn-show-more collapsed",
            ),
            Div(
                Div("soubor_velikost_od", css_class="col-sm-2"),
                Div("soubor_velikost_do", css_class="col-sm-2"),
                Div("soubor_pocet_stran_od", css_class="col-sm-2"),
                Div("soubor_pocet_stran_do", css_class="col-sm-2"),
                Div("soubor_puvodni_nazev", css_class="col-sm-2"),
                id="souboryCollapse",
                css_class="collapse row",
            ),
            Div(
                HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                HTML(vazby_divider),
                HTML(_('<hr class="mt-0" />')),
                data_toggle="collapse",
                href="#vazbyCollapse",
                role="button",
                aria_expanded="false",
                aria_controls="vazbyCollapse",
                css_class="col-sm-12 app-btn-show-more collapsed",
            ),
            Div(
                Div("id_vazby", css_class="col-sm-2"),
                id="vazbyCollapse",
                css_class="collapse row",
            ),
        ),
    )
    form_tag = False
