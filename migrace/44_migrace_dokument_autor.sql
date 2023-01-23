--add main autor for ordering purpose
alter table dokument
add column main_autor text;
-- update main autor from osoba and poradi=1
UPDATE dokument
SET main_autor = o.prijmeni
from dokument d
    join dokument_autor da on da.dokument = d.id
    join osoba o on o.id = da.autor
where da.poradi = 1
    and dokument.id = d.id;