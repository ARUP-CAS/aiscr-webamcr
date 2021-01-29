from django.urls import path

from . import views

app_name = "arch_z"

urlpatterns = [
    path("detail/<str:ident_cely>", views.detail, name="arch_z_detail"),
]
