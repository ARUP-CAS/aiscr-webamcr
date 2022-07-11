from django.urls import path

from .views import UzivatelAutocomplete

app_name = "uzivatel"

urlpatterns = [
    path(
        "seznam-uzivatele/",
        UzivatelAutocomplete.as_view(),
        name="uzivatel-autocomplete",
    )
]
