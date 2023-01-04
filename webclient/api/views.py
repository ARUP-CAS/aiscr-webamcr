from rest_framework import permissions
from rest_framework.generics import RetrieveAPIView

from dokument.models import Dokument
from .renderers import OIAPMHRenderer
from .serializers import DokumentSerializer


class DokumentView(RetrieveAPIView):
    queryset = Dokument.objects.all()
    serializer_class = DokumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = (OIAPMHRenderer,)

    def get_object(self):
        return Dokument.objects.get(ident_cely="C-DD-201710000")

