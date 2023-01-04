from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "api"


urlpatterns = [
    path("", views.DokumentView.as_view(), name="instances"),
]
