from django.urls import path

from . import views

app_name = "lokalita"

urlpatterns = [
    path("", views.LokalitaIndexView.as_view(), name="index"),
    path("zapsat", views.LokalitaCreateView.as_view(), name="create"),
    path("detail/<slug:slug>", views.LokalitaDetailView.as_view(), name="detail"),
    path("edit/<slug:slug>", views.LokalitaEditView.as_view(), name="edit"),
    path("vyber", views.LokalitaListView.as_view(), name="list"),
]
