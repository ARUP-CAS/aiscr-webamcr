from django.urls import path

from . import views

app_name = "arch_z"

urlpatterns = [
    path("detail/<str:ident_cely>", views.detail, name="detail"),
    path("edit/<str:ident_cely>", views.edit, name="edit"),
    path("zapsat/<str:projekt_ident_cely>", views.zapsat, name="zapsat"),
    path("odeslat/<str:ident_cely>", views.odeslat, name="odeslat"),
    path("archivovat/<str:ident_cely>", views.archivovat, name="archivovat"),
    path("vratit/<str:ident_cely>", views.vratit, name="vratit"),
    path("smazat/<str:ident_cely>", views.smazat, name="smazat"),
    path(
        "pripojit/dokument/<str:arch_z_ident_cely>",
        views.pripojit_dokument,
        name="pripojit_dokument",
    ),
    path(
        "pripojit/dokument/<str:arch_z_ident_cely>/<str:proj_ident_cely>",
        views.pripojit_dokument,
        name="pripojit_dokument",
    ),
    path(
        "odpojit/dokument/<str:ident_cely>/<str:arch_z_ident_cely>",
        views.odpojit_dokument,
        name="odpojit_dokument",
    ),
    path("akce-get-katastr", views.post_akce2kat, name="post_akce2kat"),
    path(
        "get-pians-in-cadastre",
        views.post_ajax_get_pians,
        name="post_ajax_get_pians",
    ),
]
