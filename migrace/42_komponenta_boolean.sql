alter table "komponenta"
alter column "jistota"
set data type boolean using case
        when "jistota" = '?' then false
        else true
    end;
