from django.urls import path

from .views import RuianKatastrAutocomplete, zjisti_katastr_souradnic, zjisti_vychozi_hodnotu

app_name = "heslar"

urlpatterns = [
    path("katastry/", RuianKatastrAutocomplete.as_view(), name="katastr-autocomplete"),
    path("zjisti-katastr-souradnic/", zjisti_katastr_souradnic, name="zjisti-katastr-souradnic"),
    path("zjisti-vychozi-hodnotu/", zjisti_vychozi_hodnotu, name="get-initial-value"),
]
