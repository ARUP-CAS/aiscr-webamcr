from django.urls import path
from oznameni.views import OznamovatelCreateView

from .views import (
    ProjectPasFromEnvelopeView,
    ProjectPianFromEnvelopeView,
    ProjectTableRowView,
    ProjektAutocompleteBezZrusenych,
    ProjektListView,
    UpravitDatumOznameniView,
    ZadostUdajeOznamovatelView,
    archivovat,
    create,
    detail,
    edit,
    generovat_expertni_list,
    generovat_oznameni,
    index,
    navrhnout_ke_zruseni,
    odpojit_dokument,
    post_ajax_get_project_one,
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
    path("stav/schvalit/<str:ident_cely>", schvalit, name="projekt_schvalit"),
    path("stav/prihlasit/<str:ident_cely>", prihlasit, name="projekt_prihlasit"),
    path(
        "stav/zahajit-v-terenu/<str:ident_cely>",
        zahajit_v_terenu,
        name="projekt_zahajit_v_terenu",
    ),
    path(
        "stav/ukoncit-v-terenu/<str:ident_cely>",
        ukoncit_v_terenu,
        name="projekt_ukoncit_v_terenu",
    ),
    path("stav/uzavrit/<str:ident_cely>", uzavrit, name="projekt_uzavrit"),
    path("stav/archivovat/<str:ident_cely>", archivovat, name="projekt_archivovat"),
    path(
        "stav/navrhnout-ke-zruseni/<str:ident_cely>",
        navrhnout_ke_zruseni,
        name="projekt_navrhnout_ke_zruseni",
    ),
    path("stav/zrusit/<str:ident_cely>", zrusit, name="projekt_zrusit"),
    path("stav/vratit/<str:ident_cely>", vratit, name="projekt_vratit"),
    path(
        "stav/vratit-navrh-zruseni/<str:ident_cely>",
        vratit_navrh_zruseni,
        name="projekt_vratit_navrh_zruseni",
    ),
    path(
        "akce-get-projekt",
        post_ajax_get_project_one,
        name="post_ajax_get_project_one",
    ),
    path(
        "mapa-projekty",
        post_ajax_get_projects_limit,
        name="post_ajax_get_projects_limit",
    ),
    path(
        "mapa-pas",
        ProjectPasFromEnvelopeView.as_view(),
        name="post_ajax_get_project_pas_limit",
    ),
    path(
        "mapa-pian",
        ProjectPianFromEnvelopeView.as_view(),
        name="post_ajax_get_project_pian_limit",
    ),
    path(
        "dokument/odpojit/<str:proj_ident_cely>/<str:ident_cely>",
        odpojit_dokument,
        name="odpojit_dokument",
    ),
    path(
        "dokument/pripojit/<str:proj_ident_cely>",
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
    path(
        "autocomplete/<str:typ>",
        ProjektAutocompleteBezZrusenych.as_view(),
        name="projekt-autocomplete-bez-zrusenych",
    ),
    path(
        "radek-tabulky-odkaz",
        ProjectTableRowView.as_view(),
        name="get_projekt_table_row",
    ),
    path(
        "oznamovatel/zapsat/<str:ident_cely>",
        OznamovatelCreateView.as_view(),
        name="pridat-oznamovatele",
    ),
    path(
        "zadost-udaje-oznamovatel/<str:ident_cely>",
        ZadostUdajeOznamovatelView.as_view(),
        name="zadost-udaje-oznamovatel",
    ),
    path(
        "upravit-datum-oznameni/<str:ident_cely>",
        UpravitDatumOznameniView.as_view(),
        name="upravit-datum-oznameni",
    ),
]
