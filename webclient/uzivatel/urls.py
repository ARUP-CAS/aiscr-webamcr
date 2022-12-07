from django.urls import path

from .views import UserAccountUpdateView, UzivatelAutocomplete, update_notifications

app_name = "uzivatel"

urlpatterns = [
    path(
        "seznam-uzivatele/",
        UzivatelAutocomplete.as_view(),
        name="uzivatel-autocomplete",
    ),
    path("upravit-uzivatele/", UserAccountUpdateView.as_view(), name="update-uzivatel"),
    path("upravit-notifikace/", update_notifications, name="update-notifications")
]
