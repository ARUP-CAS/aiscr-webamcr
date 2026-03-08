Použité knihovny a licence
==========================

Knihovny jsou do aplikace instalovány s využitím systému `pip` a jako statické soubory s využitím tagu `<script>`.

Níže je přehled licencí, které knihovny v aplikaci používají.

**MIT Licence** je velmi liberální licence, která umožňuje širokou škálu použití. Umožňuje uživatelům používat, kopírovat,
upravovat, spojovat, publikovat, distribuovat, sublicencovat a/nebo prodávat kopie softwaru a dovoluje uživatelům
držet u sebe zdrojový kód, pokud v souborech softwaru zachovají původní oznámení o autorských právech a licenci.

**GNU General Public License (GPL)** je *copyleft licence*, která vyžaduje, aby modifikované verze open source
software byly distribuovány pod stejnou licencí. To znamená, že každý software, který je odvozen od kódu pod GPL,
musí být také uvolněn pod GPL, pokud je distribuován. GPL zajišťuje, že software a jeho odvozené práce zůstanou
volně dostupné a chrání autorská práva autorů.

**BSD Licence** je sada *permissive* licencí, které jsou méně restriktivní než GPL. Povolují distribuci zdrojového
i binárního kódu s málo omezeními, což znamená, že software může být použit, modifikován a distribuován pro soukromé
i komerční účely. BSD licence obvykle vyžadují pouze zachování oznámení o autorských právech a seznamů podmínek
v redistribuovaných kódech.

**Apache Software License** je *permissive* licence podobná MIT a BSD licencím, ale obsahuje klauzuli o ochraně
proti zneužití jména. To znamená, že uživatelé mohou kopírovat, modifikovat a distribuovat software,
ale nesmí používat jméno projektu nebo jeho přispěvatelů k propagaci odvozených produktů bez předchozího písemného
souhlasu. Licence také explicitně deklaruje, že software je poskytován "tak, jak je", což chrání vývojáře
před právními nároky.

**Mozilla Public License 2.0** je *copyleft* licence, která umožňuje kombinaci MPL kódu s ne-MPL kódem v jednom
projektu. Na rozdíl od GPL, MPL nevyžaduje, aby celý software byl distribuován pod MPL, pokud používá MPL kód.
To umožňuje větší flexibilitu při integraci do různých projektů. Licence chrání vývojáře a zajišťuje, že kód
zůstane otevřený a přístupný pro komunitu.

Knihovny instalované pomocí pip
-------------------------------

Tabulka obsahuje přehled knihoven použitých v projektu, které byly nainstalovány prostřednictvím systému `pip`,
a jejich příslušné licence. Každý řádek v souboru představuje jednu knihovnu a obsahuje následující informace:

1. **Název knihovny**: Toto pole obsahuje oficiální název knihovny nebo softwarového balíčku použitého v projektu.
2. **Verze**: Verze knihovny, která je v projektu použita. Verze je důležitá pro určení kompatibility a zabezpečení knihovny.
3. **Licence**: Typ licence, pod kterou je knihovna distribuována. Licence může určovat, jak může být knihovna použita, modifikována a distribuována. Některé běžné typy licencí zahrnují MIT, GPL, Apache License atd.
4. **Odkaz**: Odkaz na domovskou stránku knihovny

Tento soubor je důležitý pro porozumění právním aspektům použitých knihoven a pro zajištění, že projekt dodržuje licenční požadavky všech použitých závislostí. Je důležité pravidelně aktualizovat tento soubor, aby odrážel jakékoli změny v použitých knihovnách nebo jejich licencích.

.. list-table:: Knihovny instalované s využitím `pip`
   :widths: 25 25 25 25
   :header-rows: 1

   * - Název knihovny
     - Verze
     - Licence
     - Odkaz
@licence_table

Ostatní knihovny a závislosti
-------------------------------

Použité JavaScript knihovny a Docker image jsou uvedeny v samostatné části dokumentace.

:doc:`Docker image <12_zavislosti/docker_images>`.
:doc:`JavaScript knihovny <12_zavislosti/javascript_knihovny>`.

