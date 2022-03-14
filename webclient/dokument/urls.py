from django.urls import path

from . import views
from .views import DokumentAutocomplete, DokumentListView

app_name = "dokument"

urlpatterns = [
    path("detail/<str:ident_cely>", views.detail, name="detail"),
    path("edit/<str:ident_cely>", views.edit, name="edit"),
    path("zapsat/do-akce/<str:arch_z_ident_cely>", views.zapsat_do_akce, name="zapsat-do-akce"),
    path("zapsat/do-projektu/<str:proj_ident_cely>", views.zapsat_do_projektu, name="zapsat-do-projektu"),
    path("odeslat/<str:ident_cely>", views.odeslat, name="odeslat"),
    path("archivovat/<str:ident_cely>", views.archivovat, name="archivovat"),
    path("vratit/<str:ident_cely>", views.vratit, name="vratit"),
    path("smazat/<str:ident_cely>", views.smazat, name="smazat"),
    path("seznam-dokumenty/", DokumentAutocomplete.as_view(), name="dokument-autocomplete"),
    path("seznam-dokumenty-bez-zapsanych/", views.DokumentAutocompleteBezZapsanych.as_view(),
         name="dokument-autocomplete-bez-zapsanych"),
    # MODELY3D
    path("model", views.index_model_3D, name="index-model-3D"),
    path("model/vybrat", DokumentListView.as_view(), name="list-model-3D"),
    path("model/zapsat", views.create_model_3D, name="create-model-3D"),
    path("model/edit/<str:ident_cely>", views.edit_model_3D, name="edit-model-3D"),
    path(
        "model/detail/<str:ident_cely>", views.detail_model_3D, name="detail-model-3D"
    ),
]
