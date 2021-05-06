from django.urls import path

from .views import (
    AkceHistorieListView,
    DokumentHistorieListView,
    ProjektHistorieListView,
)

app_name = "historie"

urlpatterns = [
    path("projekt/<str:ident_cely>", ProjektHistorieListView.as_view(), name="projekt"),
    path("arch_z/<str:ident_cely>", AkceHistorieListView.as_view(), name="akce"),
    path(
        "dokument/<str:ident_cely>", DokumentHistorieListView.as_view(), name="dokument"
    ),
]
