from django.urls import path

from . import views

app_name = "oznameni"

urlpatterns = [path("", views.index, name="index")]
