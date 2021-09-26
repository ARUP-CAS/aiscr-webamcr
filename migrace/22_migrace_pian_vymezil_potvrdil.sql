alter table pian DROP CONSTRAINT pian_potvrdil_fkey;
update pian
set potvrdil = sel.ved
from (
        select au.id as ved,
            u.id as userid
        from auth_user au
            join uzivatel u on u.ident_cely = au.username
    ) as sel
where potvrdil = sel.userid;
alter table pian
ADD CONSTRAINT pian_potvrdil_fkey FOREIGN KEY (potvrdil) REFERENCES public.auth_user (id) MATCH SIMPLE
alter table pian DROP CONSTRAINT pian_vymezil_fkey;
update pian
set vymezil = sel.ved
from (
        select au.id as ved,
            u.id as userid
        from auth_user au
            join uzivatel u on u.ident_cely = au.ident_cely
    ) as sel
where vymezil = sel.userid;
alter table pian
ADD CONSTRAINT pian_vymezil_fkey FOREIGN KEY (vymezil) REFERENCES public.auth_user (id) MATCH SIMPLE