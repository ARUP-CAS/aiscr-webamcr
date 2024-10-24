from django.urls import path

from . import views

app_name = "dj"

urlpatterns = [
    path("detail/<str:typ_vazby>/<str:ident_cely>", views.detail, name="detail"),
    path("zapsat/<str:arch_z_ident_cely>", views.zapsat, name="zapsat"),
    path("smazat/<str:ident_cely>", views.smazat, name="smazat"),
    path(
        "zmenit-katastr/<str:ident_cely>",
        views.ChangeKatastrView.as_view(),
        name="zmenit-katastr",
    ),
]
