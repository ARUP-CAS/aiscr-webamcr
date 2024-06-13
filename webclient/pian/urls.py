from django.urls import path

from . import views
from .views import PianAutocomplete

app_name = "pian"

urlpatterns = [
    path("detail/<str:ident_cely>", views.detail, name="detail"),
    path("zapsat/<str:dj_ident_cely>", views.create, name="create"),
    path("stav/potvrdit/<str:dj_ident_cely>", views.potvrdit, name="potvrdit"),
    path("odpojit/<str:dj_ident_cely>", views.odpojit, name="odpojit"),
    path("autocomplete/", PianAutocomplete.as_view(), name="pian-autocomplete"),
    path("importovat", views.ImportovatPianView.as_view(), name="importovat-pian"),
    path("mapa-connections/<str:ident_cely>", views.mapa_dj, name="mapaDj"),
]
