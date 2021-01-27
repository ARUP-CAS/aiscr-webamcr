import os

from .dev import *

try:
    import gdal

    gdal_path = Path(gdal.__file__)
    OSGEO4W = os.path.join(gdal_path.parent, "osgeo")
    os.environ["OSGEO4W_ROOT"] = OSGEO4W
    os.environ["GDAL_DATA"] = os.path.join(OSGEO4W, "data", "gdal")
    os.environ["PROJ_LIB"] = os.path.join(OSGEO4W, "data", "proj")
    os.environ["PATH"] = OSGEO4W + ";" + os.environ["PATH"]
    GEOS_LIBRARY_PATH = str(os.path.join(OSGEO4W, "geos_c.dll"))
    GDAL_LIBRARY_PATH = str(os.path.join(OSGEO4W, "gdal301.dll"))
except ImportError:
    GEOS_LIBRARY_PATH = None
    GDAL_LIBRARY_PATH = None
