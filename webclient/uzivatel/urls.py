from django.urls import path

from .views import (
    UserAccountUpdateView,
    UserDeleteRequest,
    UzivatelAutocomplete,
    UzivatelAutocompletePublic,
    update_notifications,
)

app_name = "uzivatel"

urlpatterns = [
    path(
        "uzivatel/autocomplete/",
        UzivatelAutocomplete.as_view(),
        name="uzivatel-autocomplete",
    ),
    path(
        "uzivatel/autocomplete-public/",
        UzivatelAutocompletePublic.as_view(),
        name="uzivatel-autocomplete-public",
    ),
    path("uzivatel/edit/", UserAccountUpdateView.as_view(), name="update-uzivatel"),
    path("uzivatel/notifikace/edit/", update_notifications, name="update-notifications"),
    path("uzivatel/delete-request/", UserDeleteRequest.as_view(), name="delete-uzivatel-request"),
]
