from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0021_alter_permissions_action'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
DROP FUNCTION IF EXISTS public.validateline(geometry);

CREATE OR REPLACE FUNCTION public.validateline(
    eline geometry,
    epsg integer
)
RETURNS integer
LANGUAGE plpgsql
AS $function$
DECLARE
    LINE_MAX NUMERIC(8,6);
    bad_index INTEGER;
BEGIN
    -- Nastavení prahu podle EPSG
    IF epsg = 5514 THEN
        LINE_MAX := 0.11;  -- S-JTSK (v metrech)
    ELSIF epsg = 4326 THEN
        LINE_MAX := 0.000001;  -- WGS84 (v stupních)
    ELSE
        RAISE EXCEPTION 'Unsupported EPSG: %', epsg;
    END IF;

    -- Pokud má geometrie méně než 2 body
    IF ST_NumPoints(eline) < 2 THEN
        RETURN -1;
    END IF;

    -- Vyhledání příliš krátkého segmentu pomocí SQL výrazu
    SELECT i - 1 INTO bad_index
    FROM generate_series(2, ST_NumPoints(eline)) AS i
    WHERE ST_Distance(
              ST_PointN(eline, i),
              ST_PointN(eline, i - 1)
          ) < LINE_MAX
    LIMIT 1;

    RETURN COALESCE(bad_index, 0);
END;
$function$;
            """,
            reverse_sql="DROP FUNCTION public.validateline;",
        ),
        migrations.RunSQL(
            sql="""
DROP FUNCTION IF EXISTS public.validategeom(text);

CREATE OR REPLACE FUNCTION public.validategeom(geom_text text, epsg integer)
 RETURNS text
 LANGUAGE plpgsql
AS $function$
            declare 
              back text := 'valid';
              geom_type_text text;
			  coord_dim int;
              geom geometry:=null;
			  val_result int;
              bbox geometry;
    		  allowed_types text[] := ARRAY[
		        'ST_Point', 'ST_LineString', 'ST_Polygon','ST_MultiPolygon'
		      ];
            begin
				-- Výběr BBOXu podle EPSG
			    IF epsg = 5514 THEN
			        bbox := ST_MakeEnvelope(-905000, -1230000, -400000, -930000, 5514);
			    ELSIF epsg = 4326 THEN
			        bbox := ST_MakeEnvelope(5, 40, 25, 60, 4326);
			    ELSE
			        RETURN 'pian.posgtres.importovatPian.check.unsupportedEPSG';
			    END IF;
			    -- Načti geometrii s daným SRID
			    geom := ST_SetSRID(ST_GeomFromText(geom_text), epsg);

			    -- Typ a dimenze
			    geom_type_text := ST_GeometryType(geom);
			    coord_dim := ST_CoordDim(geom);
			    
  				-- 1) Typ geometrie
			    IF NOT geom_type_text = ANY(allowed_types) THEN
			        RETURN 'pian.posgtres.importovatPian.check.wrongGeometry';
			    END IF;

			    -- 2) Musí být 2D
			    IF coord_dim != 2 THEN
			        RETURN 'pian.posgtres.importovatPian.check.dimension';
			    END IF;

				-- 3) Musí být uvnitř BBOXu
			    IF NOT ST_Within(geom, bbox) THEN
			        RETURN 'pian.posgtres.importovatPian.check.BBox';
			    END IF;

    			-- 4) Validita a jednoduchost
			    IF NOT ST_IsValid(geom) THEN
			        RETURN 'pian.posgtres.importovatPian.check.wrongGeometry';
			    ELSIF NOT ST_IsSimple(geom) THEN
			        RETURN 'pian.posgtres.importovatPian.check.geometryNotSimple';
			    ELSIF ST_IsEmpty(geom) THEN
			        RETURN 'pian.posgtres.importovatPian.check.geometryIsEmpty';
			    END IF;

			    -- 5) Multipart  neprošly by některé katastry
			    --IF ST_NumGeometries(geom) > 1 THEN
			    --    RETURN 'pian.posgtres.importovatPian.check.geometryIsMultipart';
			    --END IF;

                -- 6) Validace LINESTRING
			    IF geom_type_text = 'ST_LineString' THEN
			        val_result := validateLine(geom,epsg);
			        IF val_result = -1 THEN
			            RETURN 'pian.posgtres.importovatPian.check.tooFewPoints';
			        ELSIF val_result > 0 THEN
			            RETURN 'pian.posgtres.importovatPian.check.segmentsTooShort';
			        END IF;
			    END IF;
			
			    -- 7) Validace POLYGON
			    IF geom_type_text = 'ST_Polygon' THEN
			        FOR i IN 1..ST_NRings(geom) LOOP
			            IF i = 1 THEN
			                val_result := validateLine(ST_ExteriorRing(geom),epsg);
			                IF val_result = -1 THEN
			                    RETURN 'pian.posgtres.importovatPian.check.tooFewPoints';
			                ELSIF val_result > 0 THEN
			                    RETURN 'pian.posgtres.importovatPian.check.segmentsTooShort';
			                END IF;
			            ELSE
			                val_result := validateLine(ST_InteriorRingN(geom, i - 1),epsg);
			                IF val_result = -1 THEN
			                    RETURN 'pian.posgtres.importovatPian.check.tooFewPoints';
			                ELSIF val_result > 0 THEN
			                    RETURN 'pian.posgtres.importovatPian.check.segmentsTooShort';
			                END IF;
			            END IF;
			        END LOOP;
			    END IF;			
			    RETURN back;
			exception
             when others then
              return 'pian.posgtres.importovatPian.check.wrongGeometry';
            end;
            $function$
;
            """,
            reverse_sql="DROP FUNCTION public.validategeom;",
        ),
           migrations.RunSQL(
            sql="""
CREATE OR REPLACE FUNCTION public.validate_geom_fields_trigger()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    result_wgs text;
    result_sjtsk text;
BEGIN
    -- Validace geom (EPSG: 4326)
    IF NEW.geom IS NOT NULL THEN
        result_wgs := validategeom(ST_AsText(NEW.geom), 4326);
        IF result_wgs != 'valid' THEN
            RAISE EXCEPTION 'Invalid geometry in "geom" (EPSG:4326): %', result_wgs;
        END IF;
    END IF;

    -- Validace geom_sjtsk (EPSG: 5514)
    IF NEW.geom_sjtsk IS NOT NULL THEN
        result_sjtsk := validategeom(ST_AsText(NEW.geom_sjtsk), 5514);
        IF result_sjtsk != 'valid' THEN
            RAISE EXCEPTION 'Invalid geometry in "geom_sjtsk" (EPSG:5514): %', result_sjtsk;
        END IF;
    END IF;

    RETURN NEW;
END;
$function$
;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS public.validate_geom_fields_trigger();",
        ),
                migrations.RunSQL(
            sql="""
CREATE TRIGGER trg_validate_geometries
BEFORE INSERT OR UPDATE OF geom, geom_sjtsk ON pian
FOR EACH ROW
EXECUTE FUNCTION validate_geom_fields_trigger();
            """,
            reverse_sql="DROP TRIGGER IF EXISTS trg_validate_geometries ON pian;",
        ),
    ]
    