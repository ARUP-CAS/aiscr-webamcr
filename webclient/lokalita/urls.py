from django.urls import path

from . import views

app_name = "lokalita"

urlpatterns = [
    path("", views.LokalitaIndexView.as_view(), name="index"),
    path("zapsat", views.LokalitaCreateView.as_view(), name="create"),
    path("detail/<slug:slug>/dj/create", views.LokalitaDokumentacniJednotkaCreateView.as_view(), name="create-dj"),
    path("detail/<slug:slug>/dj/<str:dj_ident_cely>", views.LokalitaDokumentacniJednotkaUpdateView.as_view(), name="detail-dj"),
    path("detail/<str:ident_cely>/dj/<str:dj_ident_cely>/komponenta/zapsat", views.LokalitaKomponentaCreateView.as_view(), name="create-komponenta"),
    path("detail/<str:ident_cely>/dj/<str:dj_ident_cely>/komponenta/detail/<str:komponenta_ident_cely>", views.LokalitaKomponentaUpdateView.as_view(), name="update-komponenta"),
    path("detail/<str:ident_cely>/dj/<str:dj_ident_cely>/pian/create", views.LokalitaPianCreateView.as_view(), name="create-pian"),
    path("detail/<str:ident_cely>/dj/<str:dj_ident_cely>/pian/update/<str:pian_ident_cely>", views.LokalitaPianUpdateView.as_view(), name="update-pian"),
    path("detail/<str:ident_cely>/dj/<str:dj_ident_cely>/adb/zapsat", views.LokalitaAdbCreateView.as_view(), name="create-adb"),
    path("detail/<slug:slug>", views.LokalitaDetailView.as_view(), name="detail"),
    path("edit/<slug:slug>", views.LokalitaEditView.as_view(), name="edit"),
    path("vyber", views.LokalitaListView.as_view(), name="list"),
]
