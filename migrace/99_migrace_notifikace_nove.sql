-- Migrace hlídacích psů
INSERT INTO watchdog_watchdog (user_id, object_id, content_type_id, created_at)
SELECT uzivatel, 
(SELECT id FROM ruian_kraj WHERE ruian_kraj.id = (SELECT kraj FROM ruian_okres WHERE ruian_okres.id = (SELECT okres FROM ruian_katastr WHERE ruian_katastr.id = notifikace_projekt.katastr))) AS kraj,
(SELECT id FROM django_content_type WHERE model = 'ruiankraj'),
NOW()
FROM notifikace_projekt GROUP BY uzivatel, kraj;
DROP TABLE notifikace_projekt;
DROP SEQUENCE notifikace_projekt_id_seq;

-- Zapnutí základních notifikací pro všechny uživatele
INSERT INTO auth_user_notification_types (usernotificationtype_id, user_id)
SELECT (SELECT id FROM uzivatel_notifikace_typ WHERE ident_cely = 'S-E-A-XX'), id FROM auth_user;
INSERT INTO auth_user_notification_types (usernotificationtype_id, user_id)
SELECT (SELECT id FROM uzivatel_notifikace_typ WHERE ident_cely = 'S-E-N-01'), id FROM auth_user;
INSERT INTO auth_user_notification_types (usernotificationtype_id, user_id)
SELECT (SELECT id FROM uzivatel_notifikace_typ WHERE ident_cely = 'S-E-N-02'), id FROM auth_user;
INSERT INTO auth_user_notification_types (usernotificationtype_id, user_id)
SELECT (SELECT id FROM uzivatel_notifikace_typ WHERE ident_cely = 'S-E-N-05'), id FROM auth_user;
INSERT INTO auth_user_notification_types (usernotificationtype_id, user_id)
SELECT (SELECT id FROM uzivatel_notifikace_typ WHERE ident_cely = 'S-E-K-01'), id FROM auth_user;
DROP TABLE notifikace;
DROP TABLE uzivatel_notifikace;
DROP SEQUENCE uzivatel_notifikace_id_seq;

-- Nastavení upozornění na nové uživatelské účty
INSERT INTO auth_user_notification_types (usernotificationtype_id, user_id)
SELECT (SELECT id FROM uzivatel_notifikace_typ WHERE ident_cely = 'E-U-04'), id FROM auth_user WHERE auth_level & 64 = 64;
ALTER TABLE auth_user DROP COLUMN auth_level;
