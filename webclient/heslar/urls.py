from django.urls import path

from .views import (
    RuianKatastrAutocomplete,
    DokumentTypAutocomplete,
    PristupnostAutocomplete,
    zjisti_katastr_souradnic,
    zjisti_vychozi_hodnotu, DokumentFormatAutocomplete,
)
from uzivatel.views import create_osoba, OsobaAutocomplete, OsobaAutocompleteChoices

app_name = "heslar"

urlpatterns = [
    path("katastry/", RuianKatastrAutocomplete.as_view(), name="katastr-autocomplete"),
    path(
        "zjisti-katastr-souradnic/",
        zjisti_katastr_souradnic,
        name="zjisti-katastr-souradnic",
    ),
    path("zjisti-vychozi-hodnotu/", zjisti_vychozi_hodnotu, name="get-initial-value"),
    path("osoba/zapsat", create_osoba, name="create_osoba"),
    path("seznam-osoby/", OsobaAutocomplete.as_view(), name="osoba-autocomplete"),
    path("dokument-typ/", DokumentTypAutocomplete.as_view(), name="dokument-typ-autocomplete"),
    path("dokument-format/", DokumentFormatAutocomplete.as_view(), name="dokument-format-autocomplete"),
    path("pristupnost/", PristupnostAutocomplete.as_view(), name="pristupnost-autocomplete"),
    path(
        "seznam-osoby-vyber/",
        OsobaAutocompleteChoices.as_view(),
        name="osoba-autocomplete-choices",
    ),
]
