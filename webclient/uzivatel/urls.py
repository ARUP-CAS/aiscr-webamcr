from django.urls import path

from . import views
from .views import OsobaAutocomplete, UzivatelAutocomplete, OsobaAutocompleteChoices

app_name = "uzivatel"

urlpatterns = [
    path("osoba/zapsat", views.create_osoba, name="create_osoba"),
    path("seznam-osoby/", OsobaAutocomplete.as_view(), name="osoba-autocomplete"),
    path("seznam-uzivatele/", UzivatelAutocomplete.as_view(), name="uzivatel-autocomplete"),
    path("seznam-uzivatele-vyber/", OsobaAutocompleteChoices.as_view(), name="osoba-autocomplete-choices"),
]
