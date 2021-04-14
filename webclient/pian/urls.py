from django.urls import path

from . import views
from .views import PianAutocomplete

app_name = "pian"

urlpatterns = [
    path("detail/", views.detail, name="detail"),
    path("list-pians/", PianAutocomplete.as_view(), name="pian-autocomplete"),
]
