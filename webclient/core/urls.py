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
        "nahrat-soubor/<int:file_id>",
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
]
