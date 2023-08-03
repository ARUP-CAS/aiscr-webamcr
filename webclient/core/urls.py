from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="home"),
    path("nahrat-soubor/odeslat", views.post_upload, name="post_upload"),
    path(
        "nahrat-soubor/projekt/<str:ident_cely>",
        views.upload_file_projekt,
        name="upload_file_projekt",
    ),
    path(
        "nahrat-soubor/dokument/<str:ident_cely>",
        views.upload_file_dokument,
        name="upload_file_dokument",
    ),
    path(
        "nahrat-soubor/<str:typ_vazby>/nahradit/<int:file_id>",
        views.update_file,
        name="update_file",
    ),
    path(
        "nahrat-soubor/pas/<str:ident_cely>",
        views.upload_file_samostatny_nalez,
        name="upload_file_pas",
    ),
    path("stahnout-soubor/<int:pk>", views.download_file, name="download_file"),
    path("smazat-soubor/<int:pk>", views.delete_file, name="delete_file"),
    path("id/<str:ident_cely>", views.redirect_ident_view, name="redirect_ident"),
    path("prodlouzit-session/", views.prolong_session, name="prolong_session"),
    path(
        "transformace-single-wgs84",
        views.tr_wgs84,
        name="tr_wgs84",
    ),
    path(
        "transformace-multi-wgs84",
        views.tr_mwgs84,
        name="tr_mwgs84",
    ),
    path(
        "zmena-sloupcu-listu",
        views.SearchListChangeColumnsView.as_view(),
        name="zmena_sloupcu_listu",
    ),
    path("stahnout-metadata/<str:model_name>/<int:pk>", views.StahnoutMetadataView.as_view(), name="stahnout_metadata"),
    path("stahnout-metadata/<str:model_name>/<str:ident_cely>", views.StahnoutMetadataIdentCelyView.as_view(), name="stahnout_metadata"),
]
