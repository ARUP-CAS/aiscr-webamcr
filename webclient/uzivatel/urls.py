from django.urls import path

from . import views
from .views import OsobaAutocomplete

app_name = "uzivatel"

urlpatterns = [
    path("osoba/create", views.create_osoba, name="create_osoba"),
    path("osoby/", OsobaAutocomplete.as_view(), name="osoba-autocomplete"),
]
