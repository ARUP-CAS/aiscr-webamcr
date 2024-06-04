--Nastaveni typ N kde neni projekt
update akce
set typ = 'N'
where projekt is null
    and typ != 'N';
--Nasteveni typ R kde je projekt
update akce
set typ = 'R'
where projekt is not null
    and (
        typ != 'R'
        or typ is null
    );
--Nastaveni not null constrain
alter table akce
alter column typ
SET NOT NULL;
--Nastaveni check
ALTER TABLE akce ADD CONSTRAINT akce_typ_check CHECK ((typ = 'N' and projekt is null) or (typ = 'R' and projekt is not null));
