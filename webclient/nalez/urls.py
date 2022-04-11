from django.urls import path
from nalez import views

app_name = "nalez"

urlpatterns = [
    path("smazat-nalez/<str:typ>/<str:ident_cely>", views.smazat_nalez, name="smazat_nalez"),
    path("edit-nalez/<str:komp_ident_cely>", views.edit_nalez, name="edit_nalez"),
]
