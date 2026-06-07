from api.views import (
    GetUserInfo,
    ObtainAuthTokenWithUpdate,
    SamostatnyNalezEvidencniCisloPatchView,
    SamostatnyNalezFotografieUploadView,
    SamostatnyNalezXmlImportView,
)
from django.urls import path

app_name = "api"

urlpatterns = [
    path("token-auth/", ObtainAuthTokenWithUpdate.as_view()),
    path("uzivatel-info/", GetUserInfo.as_view()),
    path("pas/import-xml", SamostatnyNalezXmlImportView.as_view(), name="import-xml"),
    path(
        "pas/nalez/<str:ident_cely>/evidencni-cislo",
        SamostatnyNalezEvidencniCisloPatchView.as_view(),
        name="patch-evidencni-cislo",
    ),
    path(
        "pas/nalez/<str:ident_cely>/upload-foto",
        SamostatnyNalezFotografieUploadView.as_view(),
        name="upload-foto",
    ),
]
