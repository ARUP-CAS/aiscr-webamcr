UPDATE oznamovatel SET email = projekt || '@example.cz', adresa = 'adresa_' || projekt, odpovedna_osoba = 'osoba_' || projekt, telefon = 'telefon_' || projekt, oznamovatel = 'oznamovatel_' || projekt;

UPDATE auth_user SET first_name = 'Jméno_' || id, last_name = 'Příjmení_' || id, telefon = null, osoba = null;

WITH pom AS (
	SELECT dc.id FROM dokument_cast dc
	JOIN archeologicky_zaznam az ON az.id = dc.archeologicky_zaznam
	WHERE az.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym')
)
UPDATE dokument_cast SET archeologicky_zaznam = null WHERE id IN (SELECT id FROM pom);

WITH pom AS (
	SELECT nalp.id FROM nalez_predmet nalp
	JOIN komponenta k ON k.id = nalp.komponenta
	JOIN dokumentacni_jednotka dj ON dj.komponenty = k.komponenta_vazby
	JOIN archeologicky_zaznam az ON az.id = dj.archeologicky_zaznam
	WHERE az.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym')
)
DELETE FROM nalez_predmet USING pom WHERE nalez_predmet.id = pom.id;

WITH pom AS (
	SELECT nalo.id FROM nalez_objekt nalo
	JOIN komponenta k ON k.id = nalo.komponenta
	JOIN dokumentacni_jednotka dj ON dj.komponenty = k.komponenta_vazby
	JOIN archeologicky_zaznam az ON az.id = dj.archeologicky_zaznam
	WHERE az.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym')
)
DELETE FROM nalez_objekt USING pom WHERE nalez_objekt.id = pom.id;

WITH pom AS (
	SELECT ka.id FROM komponenta_aktivita ka
	JOIN komponenta k ON k.id = ka.komponenta
	JOIN dokumentacni_jednotka dj ON dj.komponenty = k.komponenta_vazby
	JOIN archeologicky_zaznam az ON az.id = dj.archeologicky_zaznam
	WHERE az.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym')
)
DELETE FROM komponenta_aktivita USING pom WHERE komponenta_aktivita.id = pom.id;

WITH pom AS (
	SELECT k.id FROM komponenta k
	JOIN dokumentacni_jednotka dj ON dj.komponenty = k.komponenta_vazby
	JOIN archeologicky_zaznam az ON az.id = dj.archeologicky_zaznam
	WHERE az.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym')
)
DELETE FROM komponenta USING pom WHERE komponenta.id = pom.id;

WITH pom AS (
	SELECT vb.id FROM vyskovy_bod vb
	JOIN adb ON adb.dokumentacni_jednotka = vb.adb
	JOIN dokumentacni_jednotka dj ON dj.id = adb.dokumentacni_jednotka
	JOIN archeologicky_zaznam az ON az.id = dj.archeologicky_zaznam
	WHERE az.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym')
)
DELETE FROM vyskovy_bod USING pom WHERE vyskovy_bod.id = pom.id;

WITH pom AS (
	SELECT adb.dokumentacni_jednotka FROM adb
	JOIN dokumentacni_jednotka dj ON dj.id = adb.dokumentacni_jednotka
	JOIN archeologicky_zaznam az ON az.id = dj.archeologicky_zaznam
	WHERE az.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym')
)
DELETE FROM adb USING pom WHERE adb.dokumentacni_jednotka = pom.dokumentacni_jednotka;

WITH pom AS (
	SELECT dj.id FROM dokumentacni_jednotka dj
	JOIN archeologicky_zaznam az ON az.id = dj.archeologicky_zaznam
	WHERE az.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym')
)
DELETE FROM dokumentacni_jednotka USING pom WHERE dokumentacni_jednotka.id = pom.id;

WITH pom AS (
	SELECT av.id FROM akce_vedouci av
	JOIN archeologicky_zaznam az ON az.id = av.akce
	WHERE az.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym')
)
DELETE FROM akce_vedouci USING pom WHERE akce_vedouci.id = pom.id;

WITH pom AS (
	SELECT akce.archeologicky_zaznam FROM akce
	JOIN archeologicky_zaznam az ON az.id = akce.archeologicky_zaznam
	WHERE az.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym')
)
DELETE FROM akce USING pom WHERE akce.archeologicky_zaznam = pom.archeologicky_zaznam;

WITH pom AS (
	SELECT lokalita.archeologicky_zaznam FROM lokalita
	JOIN archeologicky_zaznam az ON az.id = lokalita.archeologicky_zaznam
	WHERE az.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym')
)
DELETE FROM lokalita USING pom WHERE lokalita.archeologicky_zaznam = pom.archeologicky_zaznam;

WITH pom AS (
	SELECT his.id FROM historie his
	JOIN archeologicky_zaznam az ON az.historie = his.vazba
	WHERE az.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym')
)
DELETE FROM historie USING pom WHERE historie.id = pom.id;

WITH pom AS (
	SELECT eo.id FROM externi_odkaz eo
	JOIN archeologicky_zaznam az ON az.id = eo.archeologicky_zaznam
	WHERE az.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym')
)
DELETE FROM externi_odkaz USING pom WHERE externi_odkaz.id = pom.id;

WITH pom AS (
	SELECT kat.id FROM archeologicky_zaznam_katastr kat
	JOIN archeologicky_zaznam az ON az.id = kat.archeologicky_zaznam_id
	WHERE az.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym')
)
DELETE FROM archeologicky_zaznam_katastr USING pom WHERE archeologicky_zaznam_katastr.id = pom.id;

DELETE FROM archeologicky_zaznam az
	WHERE az.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym');

WITH pom AS (
	SELECT his.id FROM historie his
	JOIN samostatny_nalez sn ON sn.historie = his.vazba
	WHERE sn.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym')
)
DELETE FROM historie USING pom WHERE historie.id = pom.id;

DELETE FROM samostatny_nalez sn
	WHERE sn.pristupnost <> (SELECT id FROM heslar WHERE heslo = 'anonym');

WITH pom AS (
	SELECT his.id FROM historie his
	JOIN soubor ON soubor.historie = his.vazba
)
DELETE FROM historie USING pom WHERE historie.id = pom.id;

DELETE FROM soubor;

DELETE FROM notifikace_projekty_pes;
