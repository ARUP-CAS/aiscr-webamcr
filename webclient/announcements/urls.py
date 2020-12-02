from django.urls import path

from . import views

app_name = 'announcements'

urlpatterns = [
    path('announce/', views.announce, name="announce")
]
