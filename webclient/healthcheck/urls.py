from django.urls import path
from . import views

urlpatterns = [
    path("", views.healthcheck_response, name="healthcheck"),
]