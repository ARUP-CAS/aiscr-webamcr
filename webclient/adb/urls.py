from adb import views
from django.urls import path

app_name = "adb"

urlpatterns = [
    path("zapsat/<str:dj_ident_cely>", views.zapsat, name="zapsat"),
    path("smazat/<str:ident_cely>", views.smazat, name="smazat"),
    path("smazat-vb/<str:ident_cely>", views.smazat_vb, name="smazat-vb"),
]
