from django.urls import path

from . import views
from .views import ProjektListView

app_name = "projekt"

urlpatterns = [
    path("detail/<str:ident_cely>", views.detail, name="projekt_detail"),
    path("edit/<str:ident_cely>", views.edit, name="projekt_edit"),
    path("list", ProjektListView.as_view(), name="projekt_list"),
    path("schvalit/<str:ident_cely>", views.schvalit, name="projekt_schvalit"),
    path("prihlasit/<str:ident_cely>", views.prihlasit, name="projekt_prihlasit"),
    path(
        "zahajit-v-terenu/<str:ident_cely>",
        views.zahajit_v_terenu,
        name="projekt_zahajit_v_terenu",
    ),
    path(
        "ukoncit-v-terenu/<str:ident_cely>",
        views.ukoncit_v_terenu,
        name="projekt_ukoncit_v_terenu",
    ),
    path("uzavrit/<str:ident_cely>", views.uzavrit, name="projekt_uzavrit"),
    path("archivovat/<str:ident_cely>", views.archivovat, name="projekt_archivovat"),
    path(
        "navrhnout-ke-zruseni/<str:ident_cely>",
        views.navrhnout_ke_zruseni,
        name="projekt_navrhnout_ke_zruseni",
    ),
    path("zrusit/<str:ident_cely>", views.zrusit, name="projekt_zrusit"),
    path("vratit/<str:ident_cely>", views.vratit, name="projekt_vratit"),
]
