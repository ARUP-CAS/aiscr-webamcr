
alter table dokument_jazyk add column id serial;
ALTER TABLE dokument_jazyk DROP CONSTRAINT dokument_jazyk_pkey;
ALTER TABLE dokument_jazyk ADD PRIMARY KEY (id);

alter table dokument_posudek add column id serial;
ALTER TABLE dokument_posudek DROP CONSTRAINT dokument_posudek_pkey;
ALTER TABLE dokument_posudek ADD PRIMARY KEY (id);
