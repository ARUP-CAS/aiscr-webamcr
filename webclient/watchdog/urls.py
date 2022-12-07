from django.contrib.auth.decorators import login_required
from django.urls import path

from .views import WatchdogCreateView, list, delete

app_name = "watchdog"

urlpatterns = [
    path("", list, name='list'),
    path("create/", login_required(WatchdogCreateView.as_view()), name='create'),
    path("delete/<str:pk>", delete, name='delete')
]
