CORE news_feed
==============

Modul news_feed.

Přehled modulu
--------------

Data model novinkového kanálu.

Modul definuje dataclass NewsItem pro reprezentaci položky novinkového kanálu.
Tato třída je používána pro standardizaci struktury novinek z externího zdroje.

Data kanálu se načítají z repozitáře aiscr-news a považují se za
důvěryhodný obsah. Pole html se vykresluje jako důvěryhodné HTML,
protože je generuje a publikuje kontrolovaný repozitář aiscr-news.

Bezpečnostní upozornění: HTML obsah je sanitizován pomocí knihovny bleach
pro odstranění potenciálně nebezpečných prvků (scripty, event handlers atd.).
Pokud se zdroj kanálu změní nebo zdrojní repozitář nebude kontrolován,
je nutné přezkoumat konfiguraci sanitizace.

Třídy
------

.. py:class:: NewsItem

   Představuje jednu novinku z kanálu.


Funkce
------

.. py:function:: _log_warning_rate_limited(slug, message)

   Logs a warning only once per hour for the same slug.

.. py:function:: _parse_item(item_data)

   Parsuje jeden záznam novinky.

   Pokud chybí nebo je neplatný datum, název nebo úvodní text, použije se
   překladovaný placeholder pro název a pole excerpt i date zůstanou prázdná.
   Položka se ponechá a v případě problému do logu se zapíše varování.

.. py:function:: _parse_feed(data)

   Zpracuje data kanálu na seznam novinek.

.. py:function:: sanitize_html(html)

   Sanitize HTML using bleach library.

   Removes potentially dangerous HTML elements while preserving safe content.
   This is used to sanitize HTML from the news feed before rendering.

   :param html: Raw HTML string from the feed
   :return: Sanitized HTML string

.. py:function:: _process_authors(authors_data)

   Inicializuje seznam autorů.
