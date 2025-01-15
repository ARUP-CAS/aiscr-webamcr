from django.urls import path

from .views import VypisListView, VypisOnlyView, VypisView

app_name = "vypis"

urlpatterns = [
    path("<str:typ_vazby>/<str:ident_cely>/", VypisView.as_view(), name="vypis"),
    path("cisty/<str:typ_vazby>/<str:ident_cely>/", VypisOnlyView.as_view(), name="vypis_only"),
    path("list/<str:typ_vazby>/<str:identy_cele>/", VypisListView.as_view(), name="vypisy"),
]
