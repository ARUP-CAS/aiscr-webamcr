Přihlašovací stránka
===================

Přihlašovací stránka umožňuje uživatelům autentizaci do systému WebAMČR.

Správa textů
------------

Texty pro **Popis projektu** a **Novinky** jsou spravovány přes translations tagy:

* Popis projektu - ``loginPage.popisProjektu.text``
* Novinky - ``loginPage.novinky.text``

Texty mohou obsahovat HTML tagy pro stylování.

Příklad textu pro zobrazení
----------------------------

Popis projektu
~~~~~~~~~~~~~~

.. code-block:: html

   <p>
   Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus luctus massa neque. Nunc suscipit magna dui, quis molestie elit laoreet non. Aenean in tellus ut metus cursus dapibus sit amet sit amet dolor. Nulla lectus orci, fringilla vitae fringilla et, bibendum et nibh. Donec finibus sapien urna, eget laoreet sem tincidunt placerat. Aenean porta leo quis eros aliquam, eu iaculis odio scelerisque. Curabitur sollicitudin feugiat quam.
   </p>
   <p>
   Phasellus luctus massa neque. Nunc suscipit magna dui, quis molestie elit laoreet non. Aenean in tellus ut metus cursus dapibus sit amet sit amet dolor. Nulla lectus orci, fringilla vitae fringilla et, bibendum et nibh. Donec finibus sapien urna, eget laoreet sem tincidunt placerat. Aenean porta leo quis eros aliquam, eu iaculis odio scelerisque. Curabitur sollicitudin feugiat quam.
   </p>

Novinky
~~~~~~~

.. code-block:: html

   <p>
     <span>14.2.2021</span><span class="app-pipe"></span>Tisíce leteckých fotek online. V průběhu posledního týdne
     došlo ke zveřejnění zásadního souboru dokumentace, kterým je kompletní letecký archiv snímků pořízených Martinem
     Gojdou, předním odborníkem na leteckou archeologii. Sbírka čítá téměř 16 tisíc snímků, které nyní můžete snadno
     procházet v Digitálním archivu AMČR!
   </p>
   <p>
     <span>14.2.2021</span><span class="app-pipe"></span>Tisíce leteckých fotek online. V průběhu posledního týdne
     došlo ke zveřejnění zásadního souboru dokumentace, kterým je kompletní letecký archiv snímků pořízených Martinem
     Gojdou, předním odborníkem na leteckou archeologii. Sbírka čítá téměř 16 tisíc snímků, které nyní můžete snadno
     procházet v Digitálním archivu AMČR!
   </p>

