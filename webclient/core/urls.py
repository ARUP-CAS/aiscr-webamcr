from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="home"),
    path("upload-file/post", views.post_upload, name="post_upload"),
    path(
        "upload_file/projekt/<str:ident_cely>",
        views.upload_file_projekt,
        name="upload_file_projekt",
    ),
    path(
        "upload_file/dokument/<str:ident_cely>",
        views.upload_file_dokument,
        name="upload_file_dokument",
    ),
    path("download_file/<int:pk>", views.download_file, name="download_file"),
    path("delete_file/<int:pk>", views.delete_file, name="delete_file"),
]
