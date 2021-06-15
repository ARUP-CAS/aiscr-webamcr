from django.urls import path
from pas import views
from pas.views import SamostatnyNalezListView

app_name = "pas"

urlpatterns = [
    path("", views.index, name="index"),
    path("create", views.create, name="create"),
    path("detail/<str:ident_cely>", views.detail, name="detail"),
    path("list", SamostatnyNalezListView.as_view(), name="list"),
    path("smazat/<str:ident_cely>", views.smazat, name="smazat"),
]
