from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0002_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION public.validateline(
                eline geometry)
                RETURNS double precision
                LANGUAGE 'plpgsql'
                COST 100
                VOLATILE PARALLEL UNSAFE
            AS $BODY$
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
            $BODY$;
            """,
            reverse_sql="DROP FUNCTION public.validateline;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION public.validategeom(
                geom_text text)
                RETURNS text
                LANGUAGE 'plpgsql'
                COST 100
                VOLATILE PARALLEL UNSAFE
            AS $BODY$
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
            $BODY$;
            """,
            reverse_sql="DROP FUNCTION public.validategeom;",
        ),
    ]
    