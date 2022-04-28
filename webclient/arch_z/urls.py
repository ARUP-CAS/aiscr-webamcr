from django.urls import path

from . import views

app_name = "arch_z"

urlpatterns = [
    path("akce/detail/<str:ident_cely>", views.detail, name="detail"),
    path("akce/edit/<str:ident_cely>", views.edit, name="edit"),
    path("akce/zapsat/<str:projekt_ident_cely>", views.zapsat, name="zapsat"),
    path("akce/odeslat/<str:ident_cely>", views.odeslat, name="odeslat"),
    path("akce/archivovat/<str:ident_cely>", views.archivovat, name="archivovat"),
    path("akce/vratit/<str:ident_cely>", views.vratit, name="vratit"),
    path("akce/smazat/<str:ident_cely>", views.smazat, name="smazat"),
    path(
        "akce/pripojit/dokument/<str:arch_z_ident_cely>",
        views.pripojit_dokument,
        name="pripojit_dokument",
    ),
    path(
        "akce/pripojit/dokument/<str:arch_z_ident_cely>/<str:proj_ident_cely>",
        views.pripojit_dokument,
        name="pripojit_dokument",
    ),
    path(
        "akce/odpojit/dokument/<str:ident_cely>/<str:arch_z_ident_cely>",
        views.odpojit_dokument,
        name="odpojit_dokument",
    ),
    path("akce-zjisti-katastr", views.post_akce2kat, name="post_akce2kat"),
    path(
        "katastr-zjisti-piany",
        views.post_ajax_get_pians,
        name="post_ajax_get_pians",
    ),
    path("akce-vedouci-smazat/<int:akce_vedouci_id>", views.smazat_akce_vedoucí, name="smazat_akce_vedouci"),
]
