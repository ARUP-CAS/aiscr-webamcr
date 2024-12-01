from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from doi.doi_serializers import DokumentSerializer
from doi.forms import UpdateDocumentObjectIdentifierFileForm
from dokument.models import Dokument


class DigitalObjectIdentifierCustomAdminSite(admin.AdminSite):
    def update_doi(self, request):
        context = {
            "app_list": self.get_app_list(request),
            **self.each_context(request),
        }
        if request.method == "POST" and request.user.is_superuser:
            documents = Dokument.objects.all()[:100]
            for item in documents:
                serializer = DokumentSerializer(item)
                serializer.serialize_publish()
        context["form"] = UpdateDocumentObjectIdentifierFileForm()
        return TemplateResponse(request, "admin/doi_management/update_doi.html", context)

    def get_urls(
        self,
    ):
        return [
            path(
                "update-doi/",
                self.admin_view(self.update_doi),
                name="update_metadata",
            ),
        ] + super().get_urls()


admin.site.__class__ = DigitalObjectIdentifierCustomAdminSite
