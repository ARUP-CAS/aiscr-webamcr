create or replace function validateGeom(geom_text text)
   returns TEXT 
   language plpgsql
  as
$$
declare 
  back text:='valid';
  geom_type int:=0; --0:unknown type,1;point,2:line,3:polygon,4:multipart
  geom geometry:=null;
  geom_pt int:=0;
  coor_pt int:=0;
begin
	case 
	when position('MULTI' in geom_text) > 0 then geom_type:=4; 
	when position('POINT' in geom_text) > 0 then geom_type=1;
	when position('LINESTRING' in geom_text) > 0 then geom_type:=2;
	when position('POLYGON' in geom_text) > 0 then  geom_type:=3;
	end case;
	geom:=ST_GeomFromText(geom_text);
	if not ST_IsValid(geom) then
		back := 'Not valid';
	elsif ST_IsEmpty(geom) then
		back := 'Geometry is empty';
    elsif not ST_IsSimple(geom) then
		back := 'Geometry is not simple';
	elsif ST_NumGeometries(geom)>1 then
		back := 'Geometry is multipart';
	else
		if geom_type=2 and validateLine(geom)>0 then
				back:='Min. legth of line excesed';
		elsif geom_type=3 then
			for i in 1..ST_NRings(geom)--number of geometries
			loop
			 if i=1 then 
			 	if validateLine(ST_ExteriorRing(geom))>0 then
					back:='Min. legth of line excesed';
				end if;
			 elsif validateLine(ST_InteriorRingN(geom,i-1))>0 then
					back:='Min. legth of line excesed';
			 end if;

			end loop;
		end if;	
    end if;
 	return back;
exception
 when others then
  return 'Parse error';
end;
$$
