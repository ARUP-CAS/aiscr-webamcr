from rest_framework import serializers

from dokument.models import Dokument


class DokumentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Dokument
        fields = ["oai_pmh_metadata"]
