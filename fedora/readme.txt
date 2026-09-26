Fedora ukládá data do adresáře fedora/fcrepo-home
Pro vymazání Fedory je potřeba obsah tohoto adresáře vymazat a restartovat kontejner.
Fedora ukládá indexy (containment, membership, references, search) do PostgreSQL databáze
(kontejner fcrepo-postgres) už od verze 6, ale teprve od verze 7 je pro vymazání Fedory nutné
smazat i obsah této databáze (dřív stačilo smazat jen adresář fcrepo-home).
Uživatelské účty se ukládají v secrets v souboru tomcat-users.xml. Vzor souboru je v conf/tomcat-users.xml 