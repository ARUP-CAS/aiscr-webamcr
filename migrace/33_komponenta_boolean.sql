alter table "komponenta"
alter column "jistota"
set data type boolean using case
        when "jistota" isnull then true
        when "jistota" = '?' then false
    end;