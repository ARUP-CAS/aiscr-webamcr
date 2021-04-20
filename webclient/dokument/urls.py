from django.urls import path

from . import views

app_name = "dokument"

urlpatterns = [
    path("detail/<str:ident_cely>", views.detail, name="detail"),
    path("edit/<str:ident_cely>", views.edit, name="edit"),
    path("zapsat/<str:arch_z_ident_cely>", views.zapsat, name="zapsat"),
]
