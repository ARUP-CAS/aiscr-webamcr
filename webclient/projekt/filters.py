import django_filters as filters
from core.constants import OZNAMENI_PROJ, SCHVALENI_OZNAMENI_PROJ
from django.forms import DateInput, SelectMultiple
from django_filters import DateFilter, ModelMultipleChoiceFilter, MultipleChoiceFilter
from heslar.hesla import HESLAR_KULTURNI_PAMATKA, HESLAR_TYP_PROJEKTU
from heslar.models import Heslar
from projekt.models import Projekt
from uzivatel.models import Organizace, Osoba


class ProjektFilter(filters.FilterSet):
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
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_TYP_PROJEKTU),
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
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_KULTURNI_PAMATKA),
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
