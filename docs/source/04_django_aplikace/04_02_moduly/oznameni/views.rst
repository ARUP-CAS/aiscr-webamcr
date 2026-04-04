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

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``SessionIdentifier()``, ``dispatch()``, vstupuje do návratové hodnoty.
      - ``args``: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``dispatch()``, pracuje se s atributy ``pop``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``dispatch()``.



.. py:class:: OznameniZapsatView

   Třída pohledu pro 1. stranu oznámení.

   **Metody:**

   .. py:method:: post()

      Funkce pohledu pro oznámení. Oznámení je dvoustupňové.

      V prvém kroku uživatel zadává údaje a v druhém je potvrzuje a případně uploaduje soubory.

      **Parametry:**

      - ``request``: Parametr ``request`` se předává do volání ``OznamovatelForm()``, ``ProjektOznameniForm()``, pracuje se s atributy ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.

      **Výjimky:**

      - ``PermissionDenied``: Vyvolá se v konkrétních chybových větvích této funkce.


   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``render()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``render()``.

      **Výjimky:**

      - ``PermissionDenied``: Vyvolá se při splnění podmínky ``not projekty``; nebo při splnění podmínky ``cache_project is not None and self.ident_cely == cache_project``.



.. py:class:: OznameniDokumentaceView

   Třída pohledu pro 2. stranu oznámení.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``debug()``, ``get()``, pracuje se s atributy ``POST``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací výsledek volání ``redirect()``.

      **Výjimky:**

      - ``PermissionDenied``: Vyvolá se v konkrétních chybových větvích této funkce.


   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``render()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``render()``, výsledek volání ``redirect()``.

      **Výjimky:**

      - ``PermissionDenied``: Vyvolá se při splnění podmínky ``not projekt``; nebo při splnění podmínky ``cache_project is not None and self.ident_cely == cache_project``.



.. py:class:: OznameniPotvrzeniView

   Třída pohledu pro potvrzení oznámení.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``render()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``render()``, výsledek volání ``redirect()``.

      **Výjimky:**

      - ``PermissionDenied``: Vyvolá se při splnění podmínky ``not projekty``; nebo při splnění podmínky ``cache_project is not None and self.ident_cely == cache_project``.



.. py:class:: OznamovatelCreateView

   Třída pohledu pro vytvoření oznamovatele pomocí modalu.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``check_stav_changed()``, ovlivňuje větvení podmínek.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render_to_response()``.


   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``check_stav_changed()``, ``OznamovatelProjektForm()``, pracuje se s atributy ``POST``, ovlivňuje větvení podmínek.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



Funkce
------

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro editaci oznamovatele.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``OznamovatelProjektForm()``, ``add_message()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.

   **Výjimky:**

   - ``PermissionDenied``: Vyvolá se při splnění podmínky ``projekt.stav == PROJEKT_STAV_ARCHIVOVANY``.


.. py:function:: post_poi2kat(request)

   Funkce pohledu pro získaní katastru podle bodu pro oznámení.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

   **Návratová hodnota:**

   Vrací výsledek volání ``JsonResponse()``.

