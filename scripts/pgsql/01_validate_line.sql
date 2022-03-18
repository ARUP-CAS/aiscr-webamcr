CREATE OR REPLACE FUNCTION validateLine(eline geometry) RETURNS float AS $inner$
	begin
		for i in 2..ST_NumPoints(eline)--number of coordinates
			loop
				if ST_Distance(ST_PointN(eline,i),ST_PointN(eline,i-1))<0.3 then
					return ST_Distance(ST_PointN(eline,2),ST_PointN(eline,1));
				end if;
			end loop;
		RETURN 0;
	END;
	$inner$ language plpgsql;