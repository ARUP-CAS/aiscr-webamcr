from django.urls import path

from . import views

app_name = "neidentakce"

urlpatterns = [
    path("edit/<slug:slug>", views.NeidentAkceEditView.as_view(), name="edit"),
]
