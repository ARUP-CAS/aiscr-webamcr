
select validateGeom('POINT(1 1)'),'valid';
select validateGeom('Point()'),'Parse error';
select validateGeom('POINT(1 1 0 2 5)'),'Parse error';
select validateGeom('POINT EMPTY'),'Geometry is empty';

select validateGeom('LINESTRING(0 0, 1 10 )'),'valid';
select validateGeom('LINESTRING (10 10, 10 30, 20 20, 0 20)'),'Geometry is not simple';
select validateGeom('LINESTRING EMPTY'),'Geometry is empty';

select validateGeom('POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))'),'valid';
select validateGeom('POLYGON ((35 10, 45 45, 15 40, 10 20, 35 10),(20 30, 35 35, 30 20, 20 30))'),'valid';

select validateGeom('MULTIPOINT ((10 40), (40 30), (20 20), (30 10))'),'Geometry is multipart';
select validateGeom('MULTIPOINT (10 40, 40 30, 20 20, 30 10)'),'Geometry is multipart';
select validateGeom('MULTILINESTRING ((10 10, 20 20, 10 40),(40 40, 30 30, 40 20, 30 10))'),'Geometry is multipart';
select validateGeom('MULTIPOLYGON (((30 20, 45 40, 10 40, 30 20)),((15 5, 40 10, 10 20, 5 10, 15 5)))'),'Geometry is multipart';
select validateGeom('MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)),((20 35, 10 30, 10 10, 30 5, 45 20, 20 35),
(30 20, 20 15, 20 25, 30 20)))'),'Geometry is multipart';
select validateGeom('GEOMETRYCOLLECTION (POINT (40 10),
LINESTRING (10 10, 20 20, 10 40),
POLYGON ((40 40, 20 45, 45 30, 40 40)))'),'Geometry is multipart';