from django.urls import path

from . import views
from .views import DokumentAutocomplete, Model3DListView, DokumentListView

app_name = "dokument"

urlpatterns = [
    path("",views.DokumentIndexView.as_view(),name="index"),
    path("detail/<str:ident_cely>", views.DokumentDetailView.as_view(), name="detail"),
    path("detail/<str:ident_cely>/cast/<str:cast_ident_cely>", views.DokumentCastDetailView.as_view(), name="detail-cast"),
    path("edit/<str:ident_cely>", views.edit, name="edit"),
    path("zapsat", views.zapsat, name="zapsat"),
    path("zapsat/do-akce/<str:arch_z_ident_cely>", views.zapsat_do_akce, name="zapsat-do-akce"),
    path("zapsat/do-projektu/<str:proj_ident_cely>", views.zapsat_do_projektu, name="zapsat-do-projektu"),
    path("odeslat/<str:ident_cely>", views.odeslat, name="odeslat"),
    path("archivovat/<str:ident_cely>", views.archivovat, name="archivovat"),
    path("vratit/<str:ident_cely>", views.vratit, name="vratit"),
    path("smazat/<str:ident_cely>", views.smazat, name="smazat"),
    path("seznam-dokumenty/", DokumentAutocomplete.as_view(), name="dokument-autocomplete"),
    path("seznam-dokumenty-bez-zapsanych/", views.DokumentAutocompleteBezZapsanych.as_view(),
         name="dokument-autocomplete-bez-zapsanych"),
    path("vyber", DokumentListView.as_view(), name="list"),
    # MODELY3D
    path("model", views.index_model_3D, name="index-model-3D"),
    path("model/vyber", Model3DListView.as_view(), name="list-model-3D"),
    path("model/zapsat", views.create_model_3D, name="create-model-3D"),
    path("model/edit/<str:ident_cely>", views.edit_model_3D, name="edit-model-3D"),
    path(
        "model/detail/<str:ident_cely>", views.detail_model_3D, name="detail-model-3D"
    ),
    path("dokument-radek-tabulky",views.get_dokument_table_row, name="get_dokument_table_row")
]
