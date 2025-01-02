from django.urls import path

from .views import VypisView

app_name = "vypis"

urlpatterns = [
    path("<str:typ_vazby>/<str:ident_cely>/", VypisView.as_view(), name="vypis"),
]
