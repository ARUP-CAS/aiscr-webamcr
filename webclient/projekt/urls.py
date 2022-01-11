from django.urls import path

from .views import index, create, edit, smazat, prihlasit, schvalit, uzavrit, archivovat, detail, zahajit_v_terenu, \
    ukoncit_v_terenu, navrhnout_ke_zruseni, zrusit, vratit, vratit_navrh_zruseni, post_ajax_get_point, \
    odebrat_sloupec_z_vychozich
from .views import ProjektListView

app_name = "projekt"

urlpatterns = [
    path("", index, name="index"),
    path("detail/<str:ident_cely>", detail, name="detail"),
    path("create", create, name="create"),
    path("edit/<str:ident_cely>", edit, name="edit"),
    path("smazat/<str:ident_cely>", smazat, name="smazat"),
    path("list", ProjektListView.as_view(), name="list"),
    path("schvalit/<str:ident_cely>", schvalit, name="projekt_schvalit"),
    path("prihlasit/<str:ident_cely>", prihlasit, name="projekt_prihlasit"),
    path(
        "zahajit-v-terenu/<str:ident_cely>",
        zahajit_v_terenu,
        name="projekt_zahajit_v_terenu",
    ),
    path(
        "ukoncit-v-terenu/<str:ident_cely>",
        ukoncit_v_terenu,
        name="projekt_ukoncit_v_terenu",
    ),
    path("uzavrit/<str:ident_cely>", uzavrit, name="projekt_uzavrit"),
    path("archivovat/<str:ident_cely>", archivovat, name="projekt_archivovat"),
    path(
        "navrhnout-ke-zruseni/<str:ident_cely>",
        navrhnout_ke_zruseni,
        name="projekt_navrhnout_ke_zruseni",
    ),
    path("zrusit/<str:ident_cely>", zrusit, name="projekt_zrusit"),
    path("vratit/<str:ident_cely>", vratit, name="projekt_vratit"),
    path(
        "vratit-navrh-zruseni/<str:ident_cely>",
        vratit_navrh_zruseni,
        name="projekt_vratit_navrh_zruseni",
    ),
    path(
        "get-points-arround-point",
        post_ajax_get_point,
        name="post_ajax_get_points",
    ),
    path(
        "odebrat-sloupec-z-vychozich",
        odebrat_sloupec_z_vychozich,
        name="odebrat_sloupec_z_vychozich",
    )
]
