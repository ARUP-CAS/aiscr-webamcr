alter table soubor
add column size_mb NUMERIC;
update soubor
set size_mb = cast(size_bytes as numeric) / 1024 / 1024;
alter table soubor
alter column size_mb
set not null;
alter table soubor drop column size_bytes;
