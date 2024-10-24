from django.urls import path

from . import views

app_name = "ez"

urlpatterns = [
    path("", views.ExterniZdrojIndexView.as_view(), name="index"),
    path("zapsat", views.ExterniZdrojCreateView.as_view(), name="create"),
    path("detail/<slug:slug>", views.ExterniZdrojDetailView.as_view(), name="detail"),
    path(
        "stav/odeslat/<str:ident_cely>",
        views.ExterniZdrojOdeslatView.as_view(),
        name="odeslat",
    ),
    path(
        "stav/vratit/<str:ident_cely>",
        views.ExterniZdrojVratitView.as_view(),
        name="vratit",
    ),
    path(
        "stav/potvrdit/<str:ident_cely>",
        views.ExterniZdrojPotvrditView.as_view(),
        name="potvrdit",
    ),
    path(
        "smazat/<str:ident_cely>",
        views.ExterniZdrojSmazatView.as_view(),
        name="smazat",
    ),
    path("edit/<slug:slug>", views.ExterniZdrojEditView.as_view(), name="edit"),
    path("vyber", views.ExterniZdrojListView.as_view(), name="list"),
    path(
        "ext-odkaz/odpojit-az/<str:ident_cely>/<int:eo_id>",
        views.ExterniOdkazOdpojitView.as_view(),
        name="odpojit_eo",
    ),
    path(
        "ext-odkaz/pripojit-az/<str:ident_cely>",
        views.ExterniOdkazPripojitView.as_view(),
        name="pripojit_eo",
    ),
    path(
        "ext-odkaz/edit/<str:typ_vazby>/<str:ident_cely>/<slug:slug>",
        views.ExterniOdkazEditView.as_view(),
        name="zmenit_eo",
    ),
    path(
        "ext-odkaz/pripojit-ez/<str:ident_cely>",
        views.ExterniOdkazPripojitDoAzView.as_view(),
        name="pripojit_eo_do_az",
    ),
    path(
        "ext-odkaz/odpojit-ez/<str:ident_cely>/<int:eo_id>",
        views.ExterniOdkazOdpojitAZView.as_view(),
        name="odpojit_eo_az",
    ),
    path(
        "autocomplete",
        views.ExterniZdrojAutocomplete.as_view(),
        name="ez-autocomplete",
    ),
    path(
        "radek-tabulky-odkaz",
        views.ExterniZdrojTableRowView.as_view(),
        name="get_ez_table_row",
    ),
    path(
        "ext-odkaz-tabulka",
        views.EzOdkazyTableView.as_view(),
        name="get_ez_odkazy_table",
    ),
]
