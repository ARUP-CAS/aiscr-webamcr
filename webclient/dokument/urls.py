from django.urls import path

from . import views
from .views import DokumentAutocomplete, DokumentListView, DokumentyAzTableView, Model3DListView, post_ajax_get_3d_limit

app_name = "dokument"

urlpatterns = [
    path("", views.DokumentIndexView.as_view(), name="index"),
    path("detail/<str:ident_cely>", views.DokumentDetailView.as_view(), name="detail"),
    path(
        "detail/<str:ident_cely>/cast/<str:cast_ident_cely>", views.DokumentCastDetailView.as_view(), name="detail-cast"
    ),
    path("cast/edit/<slug:slug>", views.DokumentCastEditView.as_view(), name="edit-cast"),
    path(
        "detail/<str:ident_cely>/komponenta/<str:komp_ident_cely>",
        views.KomponentaDokumentDetailView.as_view(),
        name="detail-komponenta",
    ),
    path(
        "detail/<str:ident_cely>/cast/<str:cast_ident_cely>/komponenta/zapsat",
        views.KomponentaDokumentCreateView.as_view(),
        name="create-komponenta",
    ),
    path("tvar/edit/<str:ident_cely>", views.TvarEditView.as_view(), name="edit-tvar"),
    path("tvar/smazat/<str:ident_cely>/<int:pk>", views.TvarSmazatView.as_view(), name="smazat-tvar"),
    path("cast/zapsat/<str:ident_cely>", views.VytvoritCastView.as_view(), name="vytvorit-cast"),
    path(
        "cast/pripojit-arch-z/<str:ident_cely>", views.DokumentCastPripojitAkciView.as_view(), name="pripojit-az-cast"
    ),
    path(
        "cast/pripojit-projekt/<str:ident_cely>",
        views.DokumentCastPripojitProjektView.as_view(),
        name="pripojit-projekt-cast",
    ),
    path("cast/odpojit/<str:ident_cely>", views.DokumentCastOdpojitView.as_view(), name="odpojit-cast"),
    path("cast/smazat/<str:ident_cely>", views.DokumentCastSmazatView.as_view(), name="smazat-cast"),
    path(
        "neident-akce/smazat/<str:ident_cely>",
        views.DokumentNeidentAkceSmazatView.as_view(),
        name="smazat-neident-akce",
    ),
    path("edit/<str:ident_cely>", views.edit, name="edit"),
    path("zapsat", views.zapsat, name="zapsat"),
    path("zapsat/do-arch-z/<str:arch_z_ident_cely>", views.zapsat_do_akce, name="zapsat-do-akce"),
    path("zapsat/do-projektu/<str:proj_ident_cely>", views.zapsat_do_projektu, name="zapsat-do-projektu"),
    path("stav/odeslat/<str:ident_cely>", views.odeslat, name="odeslat"),
    path("stav/archivovat/<str:ident_cely>", views.archivovat, name="archivovat"),
    path("stav/vratit/<str:ident_cely>", views.vratit, name="vratit"),
    path("smazat/<str:ident_cely>", views.smazat, name="smazat"),
    path("autocomplete", DokumentAutocomplete.as_view(), name="dokument-autocomplete"),
    path("vyber", DokumentListView.as_view(), name="list"),
    # MODELY3D
    path("model/", views.index_model_3D, name="index-model-3D"),
    path("model/vyber", Model3DListView.as_view(), name="list-model-3D"),
    path("model/zapsat", views.create_model_3D, name="create-model-3D"),
    path("model/edit/<str:ident_cely>", views.edit_model_3D, name="edit-model-3D"),
    path("model/detail/<str:ident_cely>", views.detail_model_3D, name="detail-model-3D"),
    path("radek-tabulky-odkaz", views.get_dokument_table_row, name="get_dokument_table_row"),
    path(
        "model/mapa-3d",
        post_ajax_get_3d_limit,
        name="post_ajax_get_3d_limit",
    ),
    path(
        "dokumenty-tabulka/<str:typ_vazby>",
        DokumentyAzTableView.as_view(),
        name="get_dokumenty_table",
    ),
]
