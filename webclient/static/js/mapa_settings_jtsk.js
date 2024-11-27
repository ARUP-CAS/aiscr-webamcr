var cuzkWMS = L.tileLayer.wms('https://services.cuzk.cz/wms/wms.asp?', { layers: 'KN', maxZoom: 18, maxNativeZoom: 18, minZoom: 11, opacity: 0.5 }),
    cuzkWMS2 = L.tileLayer.wms('https://services.cuzk.cz/wms/wms.asp?', { layers: 'prehledka_kat_uz', maxZoom: 18, maxNativeZoom: 18, minZoom: 7, opacity: 0.5 }),
    cuzkOrt = L.tileLayer.wms('	https://ags.cuzk.cz/arcgis1/services/ORTOFOTO/MapServer/WMSServer?', { layers: '0', maxZoom: 18, maxNativeZoom: 18, minZoom: 1 }),
    cuzkEL = L.tileLayer.wms('https://ags.cuzk.cz/arcgis2/services/dmr5g/ImageServer/WMSServer?', { layers: 'dmr5g:GrayscaleHillshade', maxZoom: 18, maxNativeZoom: 18, minZoom: 1 }),
    cuzkZM = L.tileLayer('https://ags.cuzk.cz/arcgis1/rest/services/ZTM/MapServer/tile/{z}/{y}/{x}?blankTile=false', { maxZoom: 18, maxNativeZoom: 13, minZoom: 0 }),
    npuOchrana = L.tileLayer.wms('https://geoportal.npu.cz/arcgis/services/Experimental/TM_proAMCR/MapServer/WMSServer?', { layers: '2,3,4,5,7,8,10,11', maxZoom: 18, maxNativeZoom: 15, minZoom: 6, format:'image/png', transparent:true }),
    cuzkZMGrey = L.tileLayer.grayscale('https://ags.cuzk.cz/arcgis1/rest/services/ZTM/MapServer/tile/{z}/{y}/{x}?blankTile=false', { maxZoom: 18, maxNativeZoom: 13, minZoom: 0 });

   

var JTSKcrs = L.extend({}, L.CRS, {
        projection: {
            project: function(latlng) {
                var coords = convertToJTSK(latlng.lng, latlng.lat, height=0)
                return L.point(coords[0], coords[1]);
            },
            unproject: function(point) {
            
                var latlng= convertToWGS84(point.x, point.y)
                return L.latLng(latlng[1], latlng[0]); 
            },
            bounds: L.bounds([ -931374.5041534386, -1265741.5915737757], [-403476.6008465581, -896504.1794262241])
        },
    
        distance: function (latlng1, latlng2) {
            var coords1 = convertToJTSK(latlng1.lng, latlng1.lat, height=0)
            var coords2 = convertToJTSK(latlng2.lng, latlng2.lat, height=0)
            return Math.sqrt(Math.pow(coords2[0]-coords1[0],2)+Math.pow(coords2[1]-coords1[1],2))
        },
        code: 'EPSG:5514',
        transformation: new L.Transformation(1, 925000, -1, -920000), 
        scale: function(zoom) {
            return 1/(2048.260096520193* Math.pow(2,-zoom));
        },
        zoom: function (scale) {
            return Math.log(2048.26009652019 * scale) / Math.log(2);
        },   
        infinite: false,
    });
    init_position=[49.84, 15.17];
    init_zoom_jtsk=8;
    zoom_jtsk=12;