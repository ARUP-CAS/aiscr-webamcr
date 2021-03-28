from django.urls import path

from . import views

app_name = "pian"

urlpatterns = [
    path("detail/", views.detail, name="pian_detail"),
]