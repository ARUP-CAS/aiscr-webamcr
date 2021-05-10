import logging

import django_filters as filters
from arch_z.models import ArcheologickyZaznam
from core.constants import (
    OBLAST_CECHY,
    OBLAST_CHOICES,
    OBLAST_MORAVA,
    OZNAMENI_PROJ,
    SCHVALENI_OZNAMENI_PROJ,
)
from django.forms import DateInput, Select, SelectMultiple
from django.utils.translation import gettext as _
from django_filters import (
    ChoiceFilter,
    DateFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
)
from heslar.hesla import (
    HESLAR_AKCE_TYP,
    HESLAR_PAMATKOVA_OCHRANA,
    HESLAR_PRISTUPNOST,
    HESLAR_PROJEKT_TYP,
)
from heslar.models import Heslar, RuianKraj, RuianOkres
from projekt.models import Projekt
from uzivatel.models import Organizace, Osoba

logger = logging.getLogger(__name__)


class ProjektFilter(filters.FilterSet):

    oblast = ChoiceFilter(
        choices=OBLAST_CHOICES,
        label=_("Oblast"),
        method="filter_by_oblast",
        widget=Select(attrs={"class": "selectpicker", "data-live-search": "true"}),
    )

    typ_projektu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PROJEKT_TYP),
        widget=SelectMultiple(attrs={"class": "selectpicker"}),
    )

    kraj = MultipleChoiceFilter(
        choices=RuianKraj.objects.all().values_list("id", "nazev"),
        label=_("Kraje"),
        field_name="hlavni_katastr__okres__kraj",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    okres = MultipleChoiceFilter(
        choices=RuianOkres.objects.all().values_list("id", "nazev"),
        label=_("Okresy"),
        field_name="hlavni_katastr__okres",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    stav = MultipleChoiceFilter(
        choices=Projekt.CHOICES,
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    datum_zahajeni = DateFilter(
        lookup_expr="gte", widget=DateInput(attrs={"data-provide": "datepicker"})
    )
    datum_ukonceni = DateFilter(
        lookup_expr="lte", widget=DateInput(attrs={"data-provide": "datepicker"})
    )

    vedouci_projektu = ModelMultipleChoiceFilter(
        queryset=Osoba.objects.all(),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    organizace = ModelMultipleChoiceFilter(
        # queryset=Organizace.objects.filter(oao=True),
        queryset=Organizace.objects.all(),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    kulturni_pamatka = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PAMATKOVA_OCHRANA),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    # Dle transakci
    datum_oznameni_od = DateFilter(
        method="filter_announced_after",
        label="Datum oznámení od",
        widget=DateInput(attrs={"data-provide": "datepicker"}),
    )
    datum_oznameni_do = DateFilter(
        method="filter_announced_before",
        label="Datum oznámení do",
        widget=DateInput(attrs={"data-provide": "datepicker"}),
    )
    datum_schvaleni_od = DateFilter(
        method="filter_approved_after",
        label="Datum schválení od",
        widget=DateInput(attrs={"data-provide": "datepicker"}),
    )
    datum_schvaleni_do = DateFilter(
        method="filter_approved_before",
        label="Datum schválení do",
        widget=DateInput(attrs={"data-provide": "datepicker"}),
    )

    # Filters by event
    akce_hlavni_vedouci = MultipleChoiceFilter(
        choices=Osoba.objects.all().values_list("id", "vypis_cely"),
        label="Hlavní vedoucí akce",
        field_name="akce__hlavni_vedouci",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    akce_datum_zahajeni = DateFilter(
        field_name="akce__datum_zahajeni",
        lookup_expr="gte",
        label="Datum zahájení akce po",
        widget=DateInput(attrs={"data-provide": "datepicker"}),
    )
    akce_datum_ukonceni = DateFilter(
        field_name="akce__datum_ukonceni",
        lookup_expr="lte",
        label="Datum ukončení akce před",
        widget=DateInput(attrs={"data-provide": "datepicker"}),
    )
    hlavni_typ_akce = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_AKCE_TYP),
        field_name="akce__hlavni_typ",
        label="Hlavní typy akce",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    pristupnost_akce = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST),
        field_name="akce__archeologicky_zaznam__pristupnost",
        label="Přístupnosti akce",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    stav_akce = MultipleChoiceFilter(
        choices=ArcheologickyZaznam.STATES,
        field_name="akce__archeologicky_zaznam__stav",
        label="Stavy záznamů akcí",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    def filter_by_oblast(self, queryset, name, value):
        if value == OBLAST_CECHY:
            return queryset.filter(ident_cely__contains="C-")
        if value == OBLAST_MORAVA:
            return queryset.filter(ident_cely__contains="M-")
        return queryset

    def filter_announced_after(self, queryset, name, value):
        return queryset.filter(historie__historie__typ_zmeny=OZNAMENI_PROJ).filter(
            historie__historie__datum_zmeny__gte=value
        )

    def filter_announced_before(self, queryset, name, value):
        return queryset.filter(historie__historie__typ_zmeny=OZNAMENI_PROJ).filter(
            historie__historie__datum_zmeny__lte=value
        )

    def filter_approved_after(self, queryset, name, value):
        return queryset.filter(
            historie__historie__typ_zmeny=SCHVALENI_OZNAMENI_PROJ
        ).filter(historie__historie__datum_zmeny__gte=value)

    def filter_approved_before(self, queryset, name, value):
        return queryset.filter(
            historie__historie__typ_zmeny=SCHVALENI_OZNAMENI_PROJ
        ).filter(historie__historie__datum_zmeny__lte=value)

    class Meta:
        model = Projekt
        fields = {
            "ident_cely": ["icontains"],
        }
