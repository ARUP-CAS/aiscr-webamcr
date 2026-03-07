DJ signály
==========

Definice signálů.

Funkce
------

.. py:function:: save_dokumentacni_jednotka(sender, instance, created)

   Metoda pro vytvoření pianu z katastru arch záznamu.

   Metoda se volá po uložením DJ.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_dokumentacni_jednotka``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param created: Parametr ``created`` ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_dokumentacni_jednotka``.

.. py:function:: pre_delete_dokumentacni_jednotka(sender, instance)

   Provádí operaci pre delete dokumentacni jednotka.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``pre_delete_dokumentacni_jednotka``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``filter()``, pracuje se s atributy ``ident_cely``, ``active_transaction``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``pre_delete_dokumentacni_jednotka``.

.. py:function:: delete_dokumentacni_jednotka(sender, instance)

   Odstraní dokumentacni jednotka.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_dokumentacni_jednotka``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_dokumentacni_jednotka``.
