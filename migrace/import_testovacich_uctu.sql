insert into auth_user (ident_cely, first_name, last_name, email, date_joined, password, is_staff, is_superuser, is_active, organizace, auth_level) values
('U-901555', 'Josef', 'Archeologicky', 'josef_archeolog@example.com', '2020-11-19 12:32:55.748946+01', 'pbkdf2_sha256$216000$1ImgwXAxMMkc$O0KOyzYo9Z/YUOhpUUf4gYFSGer1jtcjXD054Y5V+9I=', false, false, true, 315755, 2),
('U-901556', 'Josef', 'Badatelsky', 'josef_badatel@example.com', '2020-11-19 12:32:55.748946+01', 'pbkdf2_sha256$216000$1ImgwXAxMMkc$O0KOyzYo9Z/YUOhpUUf4gYFSGer1jtcjXD054Y5V+9I=', false, false, true, 315755, 1),
('U-901557', 'Josef', 'Archivarsky', 'josef_archivar@example.com', '2020-11-19 12:32:55.748946+01', 'pbkdf2_sha256$216000$1ImgwXAxMMkc$O0KOyzYo9Z/YUOhpUUf4gYFSGer1jtcjXD054Y5V+9I=', false, false, true, 315755, 16),
('U-901558', 'Jiri', 'Bartos', 'jiri.bartos@huld.io', '2020-11-19 12:32:55.748946+01', 'pbkdf2_sha256$216000$1ImgwXAxMMkc$O0KOyzYo9Z/YUOhpUUf4gYFSGer1jtcjXD054Y5V+9I=', true, true, true, 769066, 4),
('U-901559', 'Pavla', 'Jindrakova', 'pavla.jindrakova@huld.io', '2020-11-19 12:32:55.748946+01', 'pbkdf2_sha256$216000$1ImgwXAxMMkc$O0KOyzYo9Z/YUOhpUUf4gYFSGer1jtcjXD054Y5V+9I=', true, true, true, 769066, 4),
('U-901560', 'Petr', 'Kudela', 'petr.kudela@inovatika.cz', '2020-11-19 12:32:55.748946+01', 'pbkdf2_sha256$216000$cqHDpV8GRZcK$YPlNoefKQnZVWGBNyhwEa77xz6giCvyv8mzz8t65sRM=', true, true, true, 769066, 4);

-- Tenhle ucet uz na produkci je
update auth_user set is_staff = true, is_superuser = true where email = 'juraj.skvarla@spacesystems.cz';
