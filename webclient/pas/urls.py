from django.urls import path
from pas import views
from pas.views import SamostatnyNalezListView, UzivatelSpolupraceListView

app_name = "pas"

urlpatterns = [
    path("", views.index, name="index"),
    path("create", views.create, name="create"),
    path("detail/<str:ident_cely>", views.detail, name="detail"),
    path("list", SamostatnyNalezListView.as_view(), name="list"),
    path("smazat/<str:ident_cely>", views.smazat, name="smazat"),
    path("spoluprace/zadost", views.zadost, name="spoluprace_zadost"),
    path(
        "spoluprace/list", UzivatelSpolupraceListView.as_view(), name="spoluprace_list"
    ),
    path("spoluprace/aktivace/<int:pk>", views.aktivace, name="spoluprace_aktivace"),
    path(
        "spoluprace/deaktivace/<int:pk>", views.deaktivace, name="spoluprace_deaktivace"
    ),
]
