from django.urls import path

from . import views

app_name = "projekt"

urlpatterns = [
    path("detail/<str:ident_cely>", views.detail, name="projekt_detail"),
]
