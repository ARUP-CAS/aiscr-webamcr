from django.urls import path

from .views import RuianKatastrAutocomplete

app_name = "heslar"

urlpatterns = [
    path("katastry/", RuianKatastrAutocomplete.as_view(), name="katastr-autocomplete"),
]
