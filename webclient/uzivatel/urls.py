from django.urls import path

from . import views

app_name = "uzivatel"

urlpatterns = [path("osoba/create", views.create_osoba, name="create_osoba")]
