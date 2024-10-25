from django.urls import path
from pas import views
from pas.views import SamostatnyNalezListView, UzivatelSpolupraceListView

app_name = "pas"

urlpatterns = [
    path("", views.index, name="index"),
    path("zapsat", views.SamostatnyNalezCreateView.as_view(), name="create"),
    path("zapsat/<str:ident_cely>", views.SamostatnyNalezCreateView.as_view(), name="create-from-project"),
    path("zapsat/kopie/<str:ident_cely>", views.SamostatnyNalezCreateView.as_view(), name="create-copy"),
    path("detail/<str:ident_cely>", views.detail, name="detail"),
    path("edit/<str:ident_cely>", views.edit, name="edit"),
    path("ulozeni/edit/<str:ident_cely>", views.edit_ulozeni, name="edit_ulozeni"),
    path("stav/vratit/<str:ident_cely>", views.vratit, name="vratit"),
    path("stav/odeslat/<str:ident_cely>", views.odeslat, name="odeslat"),
    path("stav/potvrdit/<str:ident_cely>", views.potvrdit, name="potvrdit"),
    path("stav/archivovat/<str:ident_cely>", views.archivovat, name="archivovat"),
    path("vyber", SamostatnyNalezListView.as_view(), name="list"),
    path("smazat/<str:ident_cely>", views.smazat, name="smazat"),
    path("spoluprace/zadost", views.zadost, name="spoluprace_zadost"),
    path("spoluprace/vyber", UzivatelSpolupraceListView.as_view(), name="spoluprace_list"),
    path(
        "spoluprace/aktivace-email/<int:pk>",
        views.AktivaceEmailView.as_view(),
        name="spoluprace_aktivace_email",
    ),
    path("spoluprace/aktivovat/<int:pk>", views.aktivace, name="spoluprace_aktivace"),
    path(
        "spoluprace/deaktivovat/<int:pk>",
        views.deaktivace,
        name="spoluprace_deaktivace",
    ),
    path(
        "mapa-zjisti-katastr",
        views.post_point_position_2_katastre,
        name="post_point_position_2_katastre",
    ),
    path(
        "mapa-zjisti-katastr-geom",
        views.post_point_position_2_katastre_with_geom,
        name="post_point_position_2_katastre_with_geom",
    ),
    path("spoluprace/smazat/<int:pk>", views.smazat_spolupraci, name="spoluprace_smazani"),
]
