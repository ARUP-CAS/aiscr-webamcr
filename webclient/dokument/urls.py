from django.urls import path

from . import views
from .views import DokumentAutocomplete, Model3DListView, DokumentListView

app_name = "dokument"

urlpatterns = [
    path("",views.DokumentIndexView.as_view(),name="index"),
    path("detail/<str:ident_cely>", views.DokumentDetailView.as_view(), name="detail"),
    path("detail/<str:ident_cely>/cast/<str:cast_ident_cely>", views.DokumentCastDetailView.as_view(), name="detail-cast"),
    path("edit-cast/<slug:slug>", views.DokumentCastEditView.as_view(), name="edit-cast"),
    path("detail/<str:ident_cely>/komponenta/<str:komp_ident_cely>",views.KomponentaDokumentDetailView.as_view(),name="detail-komponenta"),
    path("detail/<str:ident_cely>/cast/<str:cast_ident_cely>/komponenta/zapsat", views.KomponentaDokumentCreateView.as_view(), name="create-komponenta"),
    path("edit-tvar/<str:ident_cely>", views.TvarEditView.as_view(), name="edit-tvar"),
    path("smazat-tvar/<str:pk>",views.TvarSmazatView.as_view(), name="smazat-tvar"),
    path("vytvorit-cast/<str:ident_cely>", views.VytvoritCastView.as_view(), name="vytvorit-cast"),
    path("pripojit-arch-z/<str:ident_cely>",views.DokumentCastPripojitAkciView.as_view(), name="pripojit-az-cast"),
    path("pripojit-projekt/<str:ident_cely>",views.DokumentCastPripojitProjektView.as_view(),name="pripojit-projekt-cast"),
    path("odpojit-cast/<str:ident_cely>",views.DokumentCastOdpojitView.as_view(),name="odpojit-cast"),
    path("smazat-cast/<str:ident_cely>", views.DokumentCastSmazatView.as_view(),name="smazat-cast"),
    path("smazat-neident-akce/<str:ident_cely>", views.DokumentNeidentAkceSmazatView.as_view(),name="smazat-neident-akce"),
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
