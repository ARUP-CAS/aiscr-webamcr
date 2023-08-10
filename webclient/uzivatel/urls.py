from django.urls import path

from .views import (
    UserAccountUpdateView,
    UzivatelAutocomplete,
    update_notifications,
    GetUserInfo,
    ObtainAuthTokenWithUpdate,
)


app_name = "uzivatel"

urlpatterns = [
    path(
        "seznam-uzivatele/",
        UzivatelAutocomplete.as_view(),
        name="uzivatel-autocomplete",
    ),
    path("upravit-uzivatele/", UserAccountUpdateView.as_view(), name="update-uzivatel"),
    path("upravit-notifikace/", update_notifications, name="update-notifications"),
    path("api/token-auth/", ObtainAuthTokenWithUpdate.as_view()),
    path("api/uzivatel-info/", GetUserInfo.as_view()),
]
