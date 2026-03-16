from core.views import post_ajax_get_pas_and_pian_limit
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="home"),
    path(
        "soubor/nahrat/odeslat/<str:typ_vazby>/<str:ident_cely>",
        views.NewFileUploadView.as_view(),
        name="post_upload",
    ),
    path(
        "soubor/nahrat/odeslat/<str:typ_vazby>/<str:ident_cely>/<int:file_id>",
        views.UpdateExistingFileUploadView.as_view(),
        name="post_upload_update",
    ),
    path(
        "soubor/nahrat/<str:typ_vazby>/nahradit/<str:ident_cely>/<int:file_id>",
        views.UpdateFileView.as_view(),
        name="update_file",
    ),
    path(
        "soubor/nahrat/<str:typ_vazby>/<str:ident_cely>",
        views.UploadFileView.as_view(),
        name="upload_file",
    ),
    path(
        "soubor/stahnout/<str:typ_vazby>/<str:ident_cely>/<int:pk>", views.DownloadFile.as_view(), name="download_file"
    ),
    path(
        "soubor/stahnout-nahled/<str:typ_vazby>/<str:ident_cely>/<int:pk>",
        views.DownloadThumbnailSmall.as_view(),
        name="download_thumbnail",
    ),
    path(
        "soubor/stahnout-nahled-DZ/<str:typ_vazby>/<str:ident_cely>/<int:pk>",
        views.DownloadThumbnailDZ.as_view(),
        name="download_thumbnail_DZ",
    ),
    path(
        "soubor/stahnout-nahled-velky/<str:typ_vazby>/<str:ident_cely>/<int:pk>",
        views.DownloadThumbnailLarge.as_view(),
        name="download_thumbnail_large",
    ),
    path("soubor/smazat/<str:typ_vazby>/<str:ident_cely>/<int:pk>", views.delete_file, name="delete_file"),
    path("soubor/smazat-DZ/<str:typ_vazby>/<str:ident_cely>/<int:pk>", views.delete_file_DZ, name="delete_file_DZ"),
    path("id/<str:ident_cely>", views.redirect_ident_view, name="redirect_ident"),
    path("session/prodlouzit/", views.prolong_session, name="prolong_session"),
    path(
        "data-historicka/stahnout/<str:model_name>/<str:ident_cely>/<str:timestamp>",
        views.StahnoutDataHistorickaView.as_view(),
        name="stahnout_data_historicka",
    ),
    path(
        "mapa-pian-pas",
        post_ajax_get_pas_and_pian_limit,
        name="post_ajax_get_pas_pian_limit",
    ),
    path("check-authentication", views.CheckUserAuthentication.as_view(), name="check_authentication"),
    path("read-temp-value", views.ReadTempValueView.as_view(), name="read_temp_value"),
    path("delete-temp-value", views.DeleteTempValueView.as_view(), name="delete_temp_value"),
    path(
        "abort-download-temp-value",
        views.AbortDownloadUpdateTempValueView.as_view(),
        name="abort_download_update_temp_value",
    ),
    path(
        "rosetta/files/import/<str:po_filter>/<str:lang_id>/<int:idx>/",
        views.TranslationImportView.as_view(),
        name="rosetta-import-file",
    ),
    path("rosetta/files/<str:po_filter>/", views.TranslationFileListWithBackupView.as_view(), name="rosetta-file-list"),
    path(
        "rosetta/files/<str:po_filter>/<str:lang_id>/<int:idx>/",
        views.TranslationFormWithBackupView.as_view(),
        name="rosetta-form",
    ),
    path(
        "rosetta/files/<str:po_filter>/<str:lang_id>/<int:idx>/download/",
        views.TranslationFileDownloadBackup.as_view(),
        name="rosetta-download-file",
    ),
    path(
        "rosetta/files/<str:po_filter>/<str:lang_id>/<int:idx>/smazat/",
        views.TranslationFileSmazatBackup.as_view(),
        name="rosetta-smazat-file",
    ),
    path("metrics", views.PrometheusMetricsView.as_view(), name="prometheus-django-metrics"),
    path(
        "application-restart",
        views.ApplicationRestartView.as_view(),
        name="application-restart",
    ),
    path(
        "data-import-progress/<str:job_id>",
        views.DataImportProgress.as_view(),
        name="data-import-progress",
    ),
    path(
        "data-import-stop/<str:job_id>",
        views.DataImportStop.as_view(),
        name="data-import-stop",
    ),
    path(
        "data-import-start/<str:job_id>",
        views.DataImportStart.as_view(),
        name="data-import-start",
    ),
    path(
        "data-import-progress-report/<str:job_id>",
        views.DataImportProgressReportView.as_view(),
        name="data-import-progress-report",
    ),
]
