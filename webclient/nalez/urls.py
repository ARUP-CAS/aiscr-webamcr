from django.urls import path
from nalez import views

app_name = "nalez"

urlpatterns = [
    path("edit/<str:komp_ident_cely>", views.edit, name="edit"),
]
