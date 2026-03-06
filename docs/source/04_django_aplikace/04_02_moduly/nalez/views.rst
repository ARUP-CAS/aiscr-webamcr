NALEZ views
===========

Definice views.

Funkce
------

.. py:function:: smazat_nalez(request, typ_vazby, typ, ident_cely)

   Funkce pohledu pro smazání nálezu předmětu nebo objektu pomocí modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param typ_vazby: Název nebo typ ``typ_vazby`` používaný pro volbu cílové logiky.
   :param typ: Název nebo typ ``typ`` používaný pro volbu cílové logiky.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: edit_nalez(request, typ_vazby, komp_ident_cely)

   Funkce pohledu pro zapsání editace nálezu předmětu a objektu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param typ_vazby: Název nebo typ ``typ_vazby`` používaný pro volbu cílové logiky.
   :param komp_ident_cely: Identifikátor ``komp_ident_cely`` používaný pro dohledání cílového záznamu.
