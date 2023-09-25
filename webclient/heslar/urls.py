from django.urls import path

from .views import (
    RuianKatastrAutocomplete,
    DokumentTypAutocomplete,
    PristupnostAutocomplete,
    zjisti_katastr_souradnic,
    zjisti_nadrazenou_hodnotu,
    zjisti_vychozi_hodnotu, DokumentFormatAutocomplete,
)
from uzivatel.views import create_osoba, OsobaAutocomplete, OsobaAutocompleteChoices

app_name = "heslar"

urlpatterns = [
    path("katastry/", RuianKatastrAutocomplete.as_view(), name="katastr-autocomplete"),
    path(
        "mapa-zjisti-katastr/",
        zjisti_katastr_souradnic,
        name="zjisti-katastr-souradnic",
    ),
    path("zjisti-vychozi-hodnotu/", zjisti_vychozi_hodnotu, name="get-initial-value"),
    path("zjisti-nadrazenou-hodnotu/", zjisti_nadrazenou_hodnotu, name="get-nadrazena-value"),
    path("osoba/zapsat", create_osoba, name="create_osoba"),
    path("osoba/autocomplete/", OsobaAutocomplete.as_view(), name="osoba-autocomplete"),
    path("dokument-typ/", DokumentTypAutocomplete.as_view(), name="dokument-typ-autocomplete"),
    path("dokument-format/", DokumentFormatAutocomplete.as_view(), name="dokument-format-autocomplete"),
    path("pristupnost/", PristupnostAutocomplete.as_view(), name="pristupnost-autocomplete"),
    path(
        "osoba/autocomplete-vyber/",
        OsobaAutocompleteChoices.as_view(),
        name="osoba-autocomplete-choices",
    ),
]
