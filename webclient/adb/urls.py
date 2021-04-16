from adb import views
from django.urls import path

app_name = "adb"

urlpatterns = [
    path("zapsat/<str:dj_ident_cely>", views.zapsat, name="zapsat"),
]
