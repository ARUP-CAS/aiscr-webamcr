from django.urls import path

from .views import OznameniDokumentaceView, OznameniPotvrzeniView, OznameniZapsatView, post_poi2kat

app_name = "oznameni"

urlpatterns = [
    path("", OznameniZapsatView.as_view(), name="index"),
    path("zapsat/<str:ident_cely>", OznameniZapsatView.as_view(), name="index"),
    path("dokumentace", OznameniDokumentaceView.as_view(), name="index2"),
    path("dokumentace/<str:ident_cely>", OznameniDokumentaceView.as_view(), name="index2"),
    path("potvrzeni/<str:ident_cely>", OznameniPotvrzeniView.as_view(), name="index3"),
    path("mapa-zjisti-katastr", post_poi2kat, name="post_poi2kat"),
]
