import logging
from collections import OrderedDict

from rest_framework import serializers
from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject

from .models import User

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer pro info o uživately.
    """

    ident_cely = serializers.CharField(label="amcr:ident_cely")
    jmeno = serializers.CharField(source="first_name", label="amcr:jmeno")
    prijmeni = serializers.CharField(source="last_name", label="amcr:prijmeni")
    email = serializers.CharField(label="amcr:email")
    osoba = serializers.SerializerMethodField(label="amcr:osoba")

    class Meta:
        model = User
        fields = ["ident_cely", "jmeno", "prijmeni", "email", "osoba"]

    def get_osoba(self, obj):
        """
        Metóda pro správne vrácení hodnot o osobe.
        """
        return {"value": str(obj.osoba) if obj.osoba else None, "idRef": obj.osoba.ident_cely if obj.osoba else ""}

    def to_representation(self, instance):
        """
        Override reprezentace do dict pro správne zobrazení label.
        """
        ret = OrderedDict()
        fields = self._readable_fields

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            # We skip `to_representation` for `None` values so that fields do
            # not have to explicitly deal with that case.
            #
            # For related fields with `use_pk_only_optimization` we need to
            # resolve the pk value.
            check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
            if check_for_none is None:
                ret[field.label] = None
            else:
                ret[field.label] = field.to_representation(attribute)

        return ret
