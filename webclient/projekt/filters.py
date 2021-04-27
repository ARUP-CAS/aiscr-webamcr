import django_filters as filters
from arch_z.models import Akce
from core.constants import (
    OBLAST_CECHY,
    OBLAST_CHOICES,
    OBLAST_MORAVA,
    OZNAMENI_PROJ,
    SCHVALENI_OZNAMENI_PROJ,
)
from django.db.models import Exists, OuterRef
from django.forms import DateInput, Select, SelectMultiple
from django.utils.translation import gettext as _
from django_filters import (
    BooleanFilter,
    ChoiceFilter,
    DateFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
)
from heslar.hesla import HESLAR_PAMATKOVA_OCHRANA, HESLAR_PROJEKT_TYP
from heslar.models import Heslar
from projekt.models import Projekt
from uzivatel.models import Organizace, Osoba


class ProjektFilter(filters.FilterSet):
    oblast = ChoiceFilter(
        choices=OBLAST_CHOICES,
        label=_("Oblast"),
        method="filter_by_oblast",
        widget=Select(attrs={"class": "selectpicker", "data-live-search": "true"}),
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

    typ_projektu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PROJEKT_TYP),
        widget=SelectMultiple(attrs={"class": "selectpicker"}),
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

    ma_akce = BooleanFilter(
        method="filter_has_no_events",
        label="Nemá projektové akce",
    )

    def filter_by_oblast(self, queryset, name, value):
        if value == OBLAST_CECHY:
            return queryset.filter(ident_cely__contains="C-")
        if value == OBLAST_MORAVA:
            return queryset.filter(ident_cely__contains="M-")
        return queryset

    def filter_has_no_events(self, queryset, name, value):
        if value:
            return queryset.filter(
                ~Exists(Akce.objects.filter(projekt__id=OuterRef("pk")))
            )
        else:
            return queryset.filter(
                Exists(Akce.objects.filter(projekt__id=OuterRef("pk")))
            )

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
