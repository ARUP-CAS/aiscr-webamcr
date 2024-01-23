-- Add zeroes to components
update komponenta set ident_cely = concat(split_part(ident_cely, '-K', 1), '-K0' ,split_part(ident_cely, '-K', 2)) WHERE NOT(ident_cely LIKE 'C-K%' OR ident_cely LIKE 'M-K%' OR ident_cely LIKE 'X-C-K%' OR ident_cely LIKE 'X-M-K%');
update komponenta set ident_cely = concat(split_part(ident_cely, '-K', 1), '-K' ,split_part(ident_cely, '-K', 2), '-K0' ,split_part(ident_cely, '-K', 3)) WHERE ident_cely LIKE 'C-K%' OR ident_cely LIKE 'M-K%' OR ident_cely LIKE 'X-C-K%' OR ident_cely LIKE 'X-M-K%';
update dokument_cast set ident_cely = concat(left(ident_cely, length(ident_cely)-2), '0' , right(ident_cely, 2));
update adb set ident_cely = concat(left(ident_cely, length(ident_cely)-4), '00' , right(ident_cely, 4));

--Remove X- from adb and change its consecutive number to permanent value
CREATE OR REPLACE PROCEDURE migrateADBIdents()
LANGUAGE plpgsql
AS $$
DECLARE
    temp_adb record;
    new_cislo int;
BEGIN
    FOR temp_adb IN select substring(ident_cely, 3, 10) as rada, cast(right(ident_cely, 6) as INTEGER) as current_ending, ident_cely as old_ident
    	from adb
    	where ident_cely like 'X-%'
    LOOP
    	RAISE NOTICE '%, %', temp_adb.rada, temp_adb.current_ending;
    	select max(cast(right(ident_cely,6) as INTEGER))+1 from adb where ident_cely like concat(temp_adb.rada, '%') into new_cislo;
    	if new_cislo is NULL then
    	    new_cislo := 1;
    	end if;
    	update adb set ident_cely = concat(temp_adb.rada, '-' , to_char(new_cislo, 'fm000000')) where ident_cely = temp_adb.old_ident;
    END LOOP;
END;
$$;

CALL migrateADBIdents();
drop procedure migrateADBIdents();

