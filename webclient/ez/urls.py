from django.urls import path

from . import views

app_name = "ez"

urlpatterns = [
    path("", views.ExterniZdrojIndexView.as_view(), name="index"),
    path("zapsat", views.ExterniZdrojCreateView.as_view(), name="create"),
    path("detail/<slug:slug>", views.ExterniZdrojDetailView.as_view(), name="detail"),
    path(
        "odeslat/<str:ident_cely>",
        views.ExterniZdrojOdeslatView.as_view(),
        name="odeslat",
    ),
    path(
        "vratit/<str:ident_cely>",
        views.ExterniZdrojVratitView.as_view(),
        name="vratit",
    ),
    path(
        "potvrdit/<str:ident_cely>",
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
        "/odpojit-externi-odkaz/<str:ident_cely>/<int:eo_id>",
        views.ExterniOdkazOdpojitView.as_view(),
        name="odpojit_eo",
    ),
    path(
        "/pripojit-externi-odkaz/<str:ident_cely>",
        views.ExterniOdkazPripojitView.as_view(),
        name="pripojit_eo",
    ),
    path(
        "edit-paginace/<slug:slug>",
        views.ExterniOdkazEditView.as_view(),
        name="zmenit_eo",
    ),
]
