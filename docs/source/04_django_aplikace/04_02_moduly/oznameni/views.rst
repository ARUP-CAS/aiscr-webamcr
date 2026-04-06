OZNAMENI views
==============

Definice views.

Třídy
------

.. py:class:: OznameniView

   Implementuje komponentu ``OznameniView`` v rámci aplikace.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``SessionIdentifier()``, ``dispatch()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, pracuje se s atributy ``pop``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``dispatch()``.


.. py:class:: OznameniZapsatView

   Třída pohledu pro 1. stranu oznámení.

   **Metody:**

   .. py:method:: post()

      Funkce pohledu pro oznámení. Oznámení je dvoustupňové.

      V prvém kroku uživatel zadává údaje a v druhém je potvrzuje a případně uploaduje soubory.

      :param request: Parametr ``request`` se předává do volání ``OznamovatelForm()``, ``ProjektOznameniForm()``, pracuje se s atributy ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.
          :raises PermissionDenied: Vyvolá se v konkrétních chybových větvích této funkce.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``render()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``render()``.
          :raises PermissionDenied: Vyvolá se při splnění podmínky ``not projekty``; nebo při splnění podmínky ``cache_project is not None and self.ident_cely == cache_project``.


.. py:class:: OznameniDokumentaceView

   Třída pohledu pro 2. stranu oznámení.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``debug()``, ``get()``, pracuje se s atributy ``POST``, ovlivňuje větvení podmínek.

          :return: Vrací výsledek volání ``redirect()``.
          :raises PermissionDenied: Vyvolá se v konkrétních chybových větvích této funkce.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``render()``, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``render()``, výsledek volání ``redirect()``.
          :raises PermissionDenied: Vyvolá se při splnění podmínky ``not projekt``; nebo při splnění podmínky ``cache_project is not None and self.ident_cely == cache_project``.


.. py:class:: OznameniPotvrzeniView

   Třída pohledu pro potvrzení oznámení.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``render()``, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``render()``, výsledek volání ``redirect()``.
          :raises PermissionDenied: Vyvolá se při splnění podmínky ``not projekty``; nebo při splnění podmínky ``cache_project is not None and self.ident_cely == cache_project``.


.. py:class:: OznamovatelCreateView

   Třída pohledu pro vytvoření oznamovatele pomocí modalu.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

          :return: Vrací proměnná ``context``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``check_stav_changed()``, ovlivňuje větvení podmínek.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render_to_response()``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``check_stav_changed()``, ``OznamovatelProjektForm()``, pracuje se s atributy ``POST``, ovlivňuje větvení podmínek.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

          :return: Vrací výsledek volání ``JsonResponse()``.


Funkce
------

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro editaci oznamovatele.

   :param request: Parametr ``request`` se předává do volání ``OznamovatelProjektForm()``, ``add_message()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``.

       :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.
       :raises PermissionDenied: Vyvolá se při splnění podmínky ``projekt.stav == PROJEKT_STAV_ARCHIVOVANY``.

.. py:function:: post_poi2kat(request)

   Funkce pohledu pro získaní katastru podle bodu pro oznámení.

   :param request: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

       :return: Vrací výsledek volání ``JsonResponse()``.
