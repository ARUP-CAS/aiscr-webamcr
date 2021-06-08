from django.urls import path

from . import views
from .views import DokumentAutocomplete

app_name = "dokument"

urlpatterns = [
    path("detail/<str:ident_cely>", views.detail, name="detail"),
    path("edit/<str:ident_cely>", views.edit, name="edit"),
    path("zapsat/<str:arch_z_ident_cely>", views.zapsat, name="zapsat"),
    path("odeslat/<str:ident_cely>", views.odeslat, name="odeslat"),
    path("archivovat/<str:ident_cely>", views.archivovat, name="archivovat"),
    path("vratit/<str:ident_cely>", views.vratit, name="vratit"),
    path("smazat/<str:ident_cely>", views.smazat, name="smazat"),
    path("dokumenty/", DokumentAutocomplete.as_view(), name="dokument-autocomplete"),
    # MODELY3D
    path("create/model", views.create_model_3D, name="create-model-3D"),
]
