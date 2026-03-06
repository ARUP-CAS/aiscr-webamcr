import logging
from collections import OrderedDict

from rest_framework import serializers
from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject

from .models import User

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    """Serializer pro info o uživately."""

    ident_cely = serializers.CharField(label="amcr:ident_cely")
    jmeno = serializers.CharField(source="first_name", label="amcr:jmeno")
    prijmeni = serializers.CharField(source="last_name", label="amcr:prijmeni")
    email = serializers.CharField(label="amcr:email")
    osoba = serializers.SerializerMethodField(label="amcr:osoba")

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = User
        fields = ["ident_cely", "jmeno", "prijmeni", "email", "osoba"]

    def get_osoba(self, obj):
        """
        Metoda pro správně vrácení hodnot o osobe.

        :param obj: Parametr ``obj`` předává se do volání ``str()``, pracuje se s atributy ``osoba``, vstupuje do návratové hodnoty.

            :return: Vrací slovník.
        """
        return {"value": str(obj.osoba) if obj.osoba else None, "idRef": obj.osoba.ident_cely if obj.osoba else ""}

    def to_representation(self, instance):
        """
        Override reprezentace do dict pro správně zobrazení label.

        :param instance: Parametr ``instance`` předává se do volání ``get_attribute()``.

            :return: Vrací proměnná ``ret``.
        """
        ret = OrderedDict()
        fields = self._readable_fields

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            # Pro hodnoty `None` přeskočíme `to_representation`, aby pole
            # nemusela tento případ řešit explicitně.
            #
            # U relačních polí s `use_pk_only_optimization` je potřeba
            # převést hodnotu primárního klíče.
            check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
            if check_for_none is None:
                ret[field.label] = None
            else:
                ret[field.label] = field.to_representation(attribute)

        return ret
