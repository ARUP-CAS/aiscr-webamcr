from django.urls import path

from . import views

app_name = "fedora"

urlpatterns = [
    path("continue-processing/<str:job_id>", views.ContinueMedataProcessing.as_view(), name="continue-processing"),
]
