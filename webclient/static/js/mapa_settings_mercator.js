var osmGrey = L.tileLayer.grayscale('http://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'OSM grey map', maxZoom: 25, maxNativeZoom: 19, minZoom: 6 }),
    cuzkWMS = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'KN', maxZoom: 25, maxNativeZoom: 20, minZoom: 17, opacity: 0.5 }),
    cuzkWMS2 = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'prehledka_kat_uz', maxZoom: 25, maxNativeZoom: 20, minZoom: 12, opacity: 0.5 }),
    cuzkOrt = L.tileLayer('http://ags.cuzk.cz/arcgis1/rest/services/ORTOFOTO_WM/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'ortofoto_wm', maxZoom: 25, maxNativeZoom: 19, minZoom: 6 }),
    cuzkEL = L.tileLayer.wms('http://ags.cuzk.cz/arcgis2/services/dmr5g/ImageServer/WMSServer?', { layers: 'dmr5g:GrayscaleHillshade', maxZoom: 25, maxNativeZoom: 20, minZoom: 6 }),
    cuzkZM = L.tileLayer('http://ags.cuzk.cz/arcgis1/rest/services/ZTM_WM/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'zmwm', maxZoom: 25, maxNativeZoom: 19, minZoom: 6 }),
    npuOchrana = L.tileLayer.wms('https://geoportal.npu.cz/arcgis/services/Experimental/TM_proAMCR/MapServer/WMSServer?', { layers: '2,3,4,5,7,8,10,11', maxZoom: 25, maxNativeZoom: 20, minZoom: 12, format:'image/png', transparent:true });

const init_zoom_mercator=7;
const zoom_mercator=9;
const init_position=[49.84, 15.17];
