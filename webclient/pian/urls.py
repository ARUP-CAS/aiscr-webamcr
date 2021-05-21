from django.urls import path

from . import views
from .views import PianAutocomplete

app_name = "pian"

urlpatterns = [
    path("create/<str:dj_ident_cely>", views.create, name="create"),
    path("odpojit/<str:dj_ident_cely>", views.odpojit, name="odpojit"),
    path("detail/<str:ident_cely>", views.detail, name="detail"),
    path("list-pians/", PianAutocomplete.as_view(), name="pian-autocomplete"),
]
