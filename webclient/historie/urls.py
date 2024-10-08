from django.urls import path

from .views import (
    AkceHistorieListView,
    DokumentHistorieListView,
    ExterniZdrojHistorieListView,
    LokalitaHistorieListView,
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
]
