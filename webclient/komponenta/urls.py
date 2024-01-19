from django.urls import path

from . import views

app_name = "komponenta"

urlpatterns = [
    path("detail/<str:typ_vazby>/<str:ident_cely>", views.detail, name="detail"),
    path("zapsat/<str:typ_vazby>/<str:dj_ident_cely>", views.zapsat, name="zapsat"),
    path("smazat/<str:typ_vazby>/<str:ident_cely>", views.smazat, name="smazat"),
]
