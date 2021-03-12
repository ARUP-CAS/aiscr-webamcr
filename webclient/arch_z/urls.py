from django.urls import path

from . import views

app_name = "arch_z"

urlpatterns = [
    path("detail/<str:ident_cely>", views.detail, name="detail"),
    path("zapsat/<str:projekt_ident_cely>", views.zapsat, name="zapsat"),
    path("odeslat/<str:ident_cely>", views.odeslat, name="odeslat"),
    path("archivovat/<str:ident_cely>", views.archivovat, name="archivovat"),
    path("vratit/<str:ident_cely>", views.vratit, name="vratit"),
    path("smazat/<int:pk>", views.smazat, name="smazat"),
]
