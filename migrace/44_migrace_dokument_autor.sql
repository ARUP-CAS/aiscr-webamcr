--add main autor for ordering purpose
alter table dokument
add column main_autor text;
-- update poradi to 1 if poradi=1 does not exist and poradi=2 exists
update dokument_autor
set poradi = 1
from dokument_autor daaa
where daaa.dokument not in (
        select da.dokument
        from dokument_autor da
        where da.poradi = 1
    )
    and daaa.poradi = 2
    and dokument_autor.id = daaa.id;
-- update poradi to 1 if poradi=1 and 2 does not exist and poradi=3 exists
update dokument_autor
set poradi = 1
from dokument_autor daaa
where daaa.dokument not in (
        select da.dokument
        from dokument_autor da
        where da.poradi = 1
    )
    and daaa.poradi = 3
    and dokument_autor.id = daaa.id;
-- update main autor from osoba and poradi=1
UPDATE dokument
SET main_autor = o.prijmeni
from dokument d
    join dokument_autor da on da.dokument = d.id
    join osoba o on o.id = da.autor
where da.poradi = 1
    and dokument.id = d.id;