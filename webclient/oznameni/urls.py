from django.urls import path

from . import views

app_name = "oznameni"

urlpatterns = [
    path("", views.index, name="index"),
    path("get-katastr-from-point", views.post_poi2kat, name="post_poi2kat"),
]
