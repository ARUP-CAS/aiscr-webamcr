from django.urls import path

from . import views
from .views import ProjektListView

app_name = "projekt"

urlpatterns = [
    path("detail/<str:ident_cely>", views.detail, name="detail"),
    path("edit/<str:ident_cely>", views.edit, name="edit"),
    path("smazat/<str:ident_cely>", views.smazat, name="smazat"),
    path("list", ProjektListView.as_view(), name="list"),
    path("schvalit/<str:ident_cely>", views.schvalit, name="projekt_schvalit"),
    path("prihlasit/<str:ident_cely>", views.prihlasit, name="projekt_prihlasit"),
    path(
        "zahajit-v-terenu/<str:ident_cely>",
        views.zahajit_v_terenu,
        name="projekt_zahajit_v_terenu",
    ),
    path(
        "ukoncit-v-terenu/<str:ident_cely>",
        views.ukoncit_v_terenu,
        name="projekt_ukoncit_v_terenu",
    ),
    path("uzavrit/<str:ident_cely>", views.uzavrit, name="projekt_uzavrit"),
    path("archivovat/<str:ident_cely>", views.archivovat, name="projekt_archivovat"),
    path(
        "navrhnout-ke-zruseni/<str:ident_cely>",
        views.navrhnout_ke_zruseni,
        name="projekt_navrhnout_ke_zruseni",
    ),
    path("zrusit/<str:ident_cely>", views.zrusit, name="projekt_zrusit"),
    path("vratit/<str:ident_cely>", views.vratit, name="projekt_vratit"),
    path(
        "vratit-navrh-zruseni/<str:ident_cely>",
        views.vratit_navrh_zruseni,
        name="projekt_vratit_navrh_zruseni",
    ),
    path("download_file/<int:pk>", views.download_file, name="download_file"),
    path("upload_file/<str:ident_cely>", views.upload_file, name="upload_file"),
    path("delete_file/<int:pk>", views.delete_file, name="delete_file"),
    path(
        "get-points-arround-point",
        views.post_ajax_get_point,
        name="post_ajax_get_points",
    ),
]
