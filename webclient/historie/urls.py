from django.urls import path

from .views import (
    AkceHistorieListView,
    DokumentHistorieListView,
    ProjektHistorieListView,
    SamostatnyNalezHistorieListView,
    SpolupraceHistorieListView,
)

app_name = "historie"

urlpatterns = [
    path("projekt/<str:ident_cely>", ProjektHistorieListView.as_view(), name="projekt"),
    path("arch_z/<str:ident_cely>", AkceHistorieListView.as_view(), name="akce"),
    path(
        "dokument/<str:ident_cely>", DokumentHistorieListView.as_view(), name="dokument"
    ),
    path("pas/<str:ident_cely>", SamostatnyNalezHistorieListView.as_view(), name="pas"),
    path(
        "spoluprace/<str:pk>",
        SpolupraceHistorieListView.as_view(),
        name="spoluprace",
    ),
]
