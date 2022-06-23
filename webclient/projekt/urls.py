from django.urls import path

from .views import (
    ProjektListView,
    archivovat,
    create,
    detail,
    edit,
    generovat_expertni_list,
    generovat_oznameni,
    index,
    navrhnout_ke_zruseni,
    odebrat_sloupec_z_vychozich,
    odpojit_dokument,
    post_ajax_get_projects_limit,
    prihlasit,
    pripojit_dokument,
    schvalit,
    smazat,
    ukoncit_v_terenu,
    uzavrit,
    vratit,
    vratit_navrh_zruseni,
    zahajit_v_terenu,
    zrusit,
)

app_name = "projekt"

urlpatterns = [
    path("", index, name="index"),
    path("detail/<str:ident_cely>", detail, name="detail"),
    path("zapsat", create, name="create"),
    path("edit/<str:ident_cely>", edit, name="edit"),
    path("smazat/<str:ident_cely>", smazat, name="smazat"),
    path("vyber", ProjektListView.as_view(), name="list"),
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
        "akce-get-projekty",
        post_ajax_get_projects_limit,
        name="post_ajax_get_projects_limit",
    ),
    path(
        "odebrat-sloupec-z-vychozich",
        odebrat_sloupec_z_vychozich,
        name="odebrat_sloupec_z_vychozich",
    ),
    path(
        "odpojit/dokument/<str:ident_cely>/<str:proj_ident_cely>",
        odpojit_dokument,
        name="odpojit_dokument",
    ),
    path(
        "pripojit/dokument/<str:proj_ident_cely>",
        pripojit_dokument,
        name="pripojit_dokument",
    ),
    path(
        "generovat-oznameni/<str:ident_cely>",
        generovat_oznameni,
        name="generovat_oznameni",
    ),
    path(
        "generovat-expertni-list/<str:ident_cely>",
        generovat_expertni_list,
        name="generovat_expertni_list",
    ),
]
