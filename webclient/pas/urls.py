from django.urls import path
from pas import views
from pas.views import SamostatnyNalezListView, UzivatelSpolupraceListView

app_name = "pas"

urlpatterns = [
    path("", views.index, name="index"),
    path("zapsat", views.create, name="create"),
    path("zapsat/<str:ident_cely>", views.create, name="create-from-project"),
    path("detail/<str:ident_cely>", views.detail, name="detail"),
    path("edit/<str:ident_cely>", views.edit, name="edit"),
    path("edit/ulozeni/<str:ident_cely>", views.edit_ulozeni, name="edit_ulozeni"),
    path("vratit/<str:ident_cely>", views.vratit, name="vratit"),
    path("odeslat/<str:ident_cely>", views.odeslat, name="odeslat"),
    path("potvrdit/<str:ident_cely>", views.potvrdit, name="potvrdit"),
    path("archivovat/<str:ident_cely>", views.archivovat, name="archivovat"),
    path("vyber", SamostatnyNalezListView.as_view(), name="list"),
    path("smazat/<str:ident_cely>", views.smazat, name="smazat"),
    path("spoluprace/zadost", views.zadost, name="spoluprace_zadost"),
    path(
        "spoluprace/vyber", UzivatelSpolupraceListView.as_view(), name="spoluprace_list"
    ),
    path("spoluprace/aktivace/<int:pk>", views.aktivace, name="spoluprace_aktivace"),
    path(
        "spoluprace/deaktivace/<int:pk>", views.deaktivace, name="spoluprace_deaktivace"
    ),
    path(
        "pas-zjisti-katastr",
        views.post_point_position_2_katastre,
        name="post_point_position_2_katastre",
    ),
    path(
        "pas-zjisti-katastr-with-geom",
        views.post_point_position_2_katastre_with_geom,
        name="post_point_position_2_katastre_with_geom",
    ),
    path(
        "spoluprace/smazat/<int:pk>", views.smazat_spolupraci, name="spoluprace_smazani"
    ),
]
