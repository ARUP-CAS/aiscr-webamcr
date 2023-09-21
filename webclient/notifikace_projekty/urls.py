from django.urls import path

from .views import PesCreateView, PesListView, PesSmazatView

app_name = "notifikace_projekty"

urlpatterns = [
    path("", PesListView.as_view(), name="list"),
    path("zapsat/", PesCreateView.as_view(), name="zapsat"),
    path("smazat/<int:pk>", PesSmazatView.as_view(), name="smazat"),
]
