from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="home"),
    path("soubor/nahrat/odeslat", views.post_upload, name="post_upload"),
    path(
        "soubor/nahrat/<str:typ_vazby>/nahradit/<str:ident_cely>/<int:file_id>",
        views.update_file,
        name="update_file",
    ),
    path(
        "soubor/nahrat/<str:typ_vazby>/<str:ident_cely>",
        views.uploadFileView.as_view(),
        name="upload_file",
    ),
    path("soubor/stahnout/<str:typ_vazby>/<str:ident_cely>/<int:pk>", views.DownloadFile.as_view(), name="download_file"),
    path("soubor/stahnout-nahled/<str:typ_vazby>/<str:ident_cely>/<int:pk>", views.DownloadThumbnail.as_view(), name="download_thumbnail"),
    path("soubor/smazat/<str:typ_vazby>/<str:ident_cely>/<int:pk>", views.delete_file, name="delete_file"),
    path("id/<str:ident_cely>", views.redirect_ident_view, name="redirect_ident"),
    path("session/prodlouzit/", views.prolong_session, name="prolong_session"),
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
        "tabulka/zmenit-sloupce",
        views.SearchListChangeColumnsView.as_view(),
        name="zmena_sloupcu_listu",
    ),
    path(
        "metadata/stahnout/<str:model_name>/<str:ident_cely>",
        views.StahnoutMetadataIdentCelyView.as_view(),
        name="stahnout_metadata",
    ),
]
