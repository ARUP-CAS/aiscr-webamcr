from django.urls import path, re_path

from . import views

from core.views import (
    post_ajax_get_pas_and_pian_limit,
)

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
        views.Uploadfileview.as_view(),
        name="upload_file",
    ),
    path("soubor/stahnout/<str:typ_vazby>/<str:ident_cely>/<int:pk>", views.DownloadFile.as_view(), name="download_file"),
    path("soubor/stahnout-nahled/<str:typ_vazby>/<str:ident_cely>/<int:pk>", views.DownloadThumbnailSmall.as_view(),
         name="download_thumbnail"),
    path("soubor/stahnout-nahled-velky/<str:typ_vazby>/<str:ident_cely>/<int:pk>",
         views.DownloadThumbnailLarge.as_view(), name="download_thumbnail_large"),
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
    path(
        "mapa-pian-pas",
        post_ajax_get_pas_and_pian_limit,
        name="post_ajax_get_pas_pian_limit",
    ),
    path("check-authentication", views.CheckUserAuthentication.as_view(), name="check_authentication"),
    path("read-temp-value", views.ReadTempValueView.as_view(), name="read_temp_value"),
    path("reset-temp-value", views.ResetTempValueView.as_view(), name="reset_temp_value"),
    path(
        "rosetta/files/import/<str:po_filter>/<str:lang_id>/<int:idx>/",
        views.TranslationImportView.as_view(),
        name="rosetta-import-file"
    ),
    path(
        "rosetta/files/<str:po_filter>/",
        views.TranslationFileListWithBackupView.as_view(),
        name="rosetta-file-list"
    ),
    path(
        "rosetta/files/<str:po_filter>/<str:lang_id>/<int:idx>/",
        views.TranslationFormWithBackupView.as_view(),
        name="rosetta-form"
    ),
    path(
        "rosetta/files/<str:po_filter>/<str:lang_id>/<int:idx>/download/",
        views.TranslationFileDownloadBackup.as_view(),
        name="rosetta-download-file"
    ),
    path(
        "rosetta/files/<str:po_filter>/<str:lang_id>/<int:idx>/smazat/",
        views.TranslationFileSmazatBackup.as_view(),
        name="rosetta-smazat-file",
    ),
    path("metrics", views.PrometheusMetricsView.as_view(), name="prometheus-django-metrics"),
    path("application-restart", views.ApplicationRestartView.as_view(), name="application-restart",)
]
