from adb import views
from django.urls import path

app_name = "adb"

urlpatterns = [
    path("detail/<str:ident_cely>", views.detail, name="detail"),
    path("zapsat/<str:dj_ident_cely>", views.zapsat, name="zapsat"),
    path("vyskove-body/zapsat/<str:adb_ident_cely>", views.zapsat_vyskove_body, name="zapsat_vyskove_body"),
    path("smazat/<str:ident_cely>", views.smazat, name="smazat"),
    path("smazat-vb/<str:ident_cely>", views.smazat_vb, name="smazat-vb"),
]
