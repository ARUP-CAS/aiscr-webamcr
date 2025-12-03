from django.urls import path

from .views import (
    AdbHistorieListView,
    AkceHistorieListView,
    DokumentHistorieListView,
    ExterniZdrojHistorieListView,
    LokalitaHistorieListView,
    PianHistorieListView,
    PianLokalitaHistorieListView,
    ProjektHistorieListView,
    SamostatnyNalezHistorieListView,
    SouborHistorieListView,
    SpolupraceHistorieListView,
    UzivatelHistorieListView,
)

app_name = "historie"

urlpatterns = [
    path("projekt/<str:ident_cely>", ProjektHistorieListView.as_view(), name="projekt"),
    path("arch-z/<str:ident_cely>", AkceHistorieListView.as_view(), name="akce"),
    path("dokument/<str:ident_cely>", DokumentHistorieListView.as_view(), name="dokument"),
    path("pas/<str:ident_cely>", SamostatnyNalezHistorieListView.as_view(), name="pas"),
    path("soubor/<int:soubor_id>", SouborHistorieListView.as_view(), name="soubor"),
    path(
        "spoluprace/<int:pk>",
        SpolupraceHistorieListView.as_view(),
        name="spoluprace",
    ),
    path("lokalita/<str:ident_cely>", LokalitaHistorieListView.as_view(), name="lokalita"),
    path("uzivatel/<str:ident_cely>", UzivatelHistorieListView.as_view(), name="uzivatel"),
    path("ez/<str:ident_cely>", ExterniZdrojHistorieListView.as_view(), name="ez"),
    path(
        "pian/<str:ident_cely>/<str:akce_ident_cely>/<str:dj_ident_cely>", PianHistorieListView.as_view(), name="pian"
    ),
    path(
        "pian-lokalita/<str:ident_cely>/<str:lokalita_ident_cely>/<str:dj_ident_cely>",
        PianLokalitaHistorieListView.as_view(),
        name="pian-lokalita",
    ),
    path("adb/<str:ident_cely>/<str:akce_ident_cely>/<str:dj_ident_cely>", AdbHistorieListView.as_view(), name="adb"),
]
