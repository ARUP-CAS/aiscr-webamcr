from django.urls import path
from nalez import views

app_name = "nalez"

urlpatterns = [
    path("edit-objekt/<str:komp_ident_cely>", views.edit_objekt, name="edit_objekt"),
    path("edit-predmet/<str:komp_ident_cely>", views.edit_predmet, name="edit_predmet"),
]
