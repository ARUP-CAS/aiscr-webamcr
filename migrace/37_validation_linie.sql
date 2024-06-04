CREATE OR REPLACE FUNCTION validateLine(eline geometry) RETURNS float AS $inner$
	declare
	LINE_MAX NUMERIC(8,6):=0.3;--SJTSK
	begin
		if ABS(ST_Y(ST_StartPoint(eline)))<400 then
			LINE_MAX=0.000001; --WGS84
		end if;
		for i in 2..ST_NumPoints(eline)--number of coordinates
			loop
				if ST_Distance(ST_PointN(eline,i),ST_PointN(eline,i-1))<LINE_MAX then
					return ST_Distance(ST_PointN(eline,2),ST_PointN(eline,1));
				end if;
			end loop;
		RETURN 0;
	END;
	$inner$ language plpgsql;
	
