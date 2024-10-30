from django.urls import path

from . import views

app_name = "arch_z"

urlpatterns = [
    path("akce/detail/<str:ident_cely>", views.ArcheologickyZaznamDetailView.as_view(), name="detail"),
    path("akce/detail/<str:ident_cely>/dj/zapsat", views.DokumentacniJednotkaCreateView.as_view(), name="create-dj"),
    path(
        "akce/detail/<str:ident_cely>/dj/<str:dj_ident_cely>",
        views.DokumentacniJednotkaUpdateView.as_view(),
        name="detail-dj",
    ),
    path(
        "akce/detail/<str:ident_cely>/dj/<str:dj_ident_cely>/komponenta/zapsat",
        views.KomponentaCreateView.as_view(),
        name="create-komponenta",
    ),
    path(
        "akce/detail/<str:ident_cely>/dj/<str:dj_ident_cely>/komponenta/detail/<str:komponenta_ident_cely>",
        views.KomponentaUpdateView.as_view(),
        name="update-komponenta",
    ),
    path(
        "akce/detail/<str:ident_cely>/dj/<str:dj_ident_cely>/pian/zapsat",
        views.PianCreateView.as_view(),
        name="create-pian",
    ),
    path(
        "akce/detail/<str:ident_cely>/dj/<str:dj_ident_cely>/pian/edit/<str:pian_ident_cely>",
        views.PianUpdateView.as_view(),
        name="update-pian",
    ),
    path(
        "akce/detail/<str:ident_cely>/dj/<str:dj_ident_cely>/adb/zapsat",
        views.AdbCreateView.as_view(),
        name="create-adb",
    ),
    path("akce/edit/<str:ident_cely>", views.edit, name="edit"),
    path("akce/zapsat/<str:projekt_ident_cely>", views.zapsat, name="zapsat"),
    path("akce/zapsat", views.zapsat, name="zapsat-akci"),
    path("stav/odeslat/<str:ident_cely>", views.odeslat, name="odeslat"),
    path("stav/archivovat/<str:ident_cely>", views.archivovat, name="archivovat"),
    path("stav/vratit/<str:ident_cely>", views.vratit, name="vratit"),
    path("akce/smazat/<str:ident_cely>", views.smazat, name="smazat"),
    path("akce/zmenit-proj-akci/<str:ident_cely>", views.ProjektAkceChange.as_view(), name="zmenit-proj-akci"),
    path("akce/zmenit-sam-akci/<str:ident_cely>", views.SamostatnaAkceChange.as_view(), name="zmenit-sam-akci"),
    path(
        "dokument/pripojit/<str:arch_z_ident_cely>",
        views.pripojit_dokument,
        name="pripojit_dokument",
    ),
    path(
        "dokument/pripojit/<str:arch_z_ident_cely>/<str:proj_ident_cely>",
        views.pripojit_dokument,
        name="pripojit_dokument",
    ),
    path(
        "dokument/odpojit/<str:arch_z_ident_cely>/<str:ident_cely>",
        views.odpojit_dokument,
        name="odpojit_dokument",
    ),
    path("mapa-zoom", views.post_akce2kat, name="post_akce2kat"),
    path(
        "akce/vedouci/smazat/<str:ident_cely>/<int:akce_vedouci_id>",
        views.smazat_akce_vedoucí,
        name="smazat_akce_vedouci",
    ),
    path(
        "mapa-pian",
        views.post_ajax_get_pians_limit,
        name="post_ajax_get_pians_limit",
    ),
    path(
        "mapa-dalsi-katastry",
        views.GetAkceOtherKatastrView.as_view(),
        name="post_ajax_get_akce_other_katastr",
    ),
    path("akce/vyber", views.AkceListView.as_view(), name="list"),
    path("akce/", views.AkceIndexView.as_view(), name="index"),
    path("autocomplete/<str:type>", views.ArchZAutocomplete.as_view(), name="arch-z-autocomplete"),
    path("radek-tabulky-odkaz", views.ArchZTableRowView.as_view(), name="get_archz_table_row"),
]
