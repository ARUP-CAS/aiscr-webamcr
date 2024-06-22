var osmColor = L.tileLayer('http://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'OSM map', maxZoom: 25, maxNativeZoom: 19, minZoom: 6 }),
    cuzkWMS = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'KN', maxZoom:25, maxNativeZoom: 20, minZoom: 17, opacity: 0.5 }),
    cuzkWMS2 = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'prehledka_kat_uz', maxZoom:25, maxNativeZoom: 20, minZoom: 12, opacity: 0.5 }),
    cuzkOrt = L.tileLayer('http://ags.cuzk.cz/arcgis1/rest/services/ORTOFOTO_WM/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'ortofoto_wm', maxZoom:25, maxNativeZoom: 19, minZoom: 6 }),
    cuzkEL = L.tileLayer.wms('http://ags.cuzk.cz/arcgis2/services/dmr5g/ImageServer/WMSServer?', { layers: 'dmr5g:GrayscaleHillshade', maxZoom: 25, maxNativeZoom: 20, minZoom: 6 }),
    cuzkZM = L.tileLayer('http://ags.cuzk.cz/arcgis1/rest/services/ZTM_WM/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'zmwm', maxZoom: 25,maxNativeZoom:19, minZoom: 6 }),
    npuOchrana = L.tileLayer.wms('https://geoportal.npu.cz/arcgis/services/Experimental/TM_proAMCR/MapServer/WMSServer?', { layers: '2,3,4,5,7,8,10,11', maxZoom: 25, maxNativeZoom: 20, minZoom: 12, format:'image/png', transparent:true });

var poi = L.layerGroup();
var map = L.map('projectMap',{attributionControl:false,zoomControl:false,  layers: [cuzkZM]}).setView([49.84, 15.17], 7);

var baseLayers = {
    [map_translations['cuzkzakladniMapyCr']]: cuzkZM,
    [map_translations['cuzkOrtofotomapa']]: cuzkOrt,
    [map_translations['cuzkStinovanyeelief5G']]: cuzkEL,
    [map_translations['openStreetMap']]: osmColor,
};

var overlays = {
    [map_translations['cuzkKatastralniMapa']]: cuzkWMS,
    [map_translations['cuzkKatastralniUzemi']]: cuzkWMS2,
    [map_translations['npuPamatkovaOchrana']]: npuOchrana,
};

var global_map_layers = L.control.layers(baseLayers,overlays).addTo(map);
L.control.scale(metric = "true").addTo(map);
map.addControl(new L.Control.Fullscreen({
    title: {
        'false': [map_translations['FullscreenTitle']],
        'true': [map_translations['FullscreenTitleClose']]
    }
}));
map.addControl(new L.control.zoom(
    {
        zoomInText: '+',
        zoomInTitle: [map_translations['zoomInTitle']],
        zoomOutText: '-',
        zoomOutTitle: [map_translations['zoomOutTitle']]
    }))

var searchControl=new L.Control.Search({
    position:'topleft',
    sourceData: searchByAjax,
    initial: false,
    zoom: 12,
    marker: false,
    textPlaceholder: [map_translations['SearchText']],
    textCancel: [map_translations['SearchTextCancel']],
    propertyName: 'text',
    propertyMagicKey:'magicKey',
    propertyMagicKeyUrl:'https://ags.cuzk.cz/arcgis/rest/services/RUIAN/Vyhledavaci_sluzba_nad_daty_RUIAN/MapServer/exts/GeocodeSOE/tables/{*}/findAddressCandidates?outSR={"wkid":4258}&f=json',
    textErr: [map_translations['SearchTextError']],
    minLength:3
}).addTo(map);

let global_measuring_toolbox=new L.control.measure(
    {
        title: [map_translations['MeasureTitle']],
        icon:'<img src="'+static_url+'img/ruler-bold-32.png" style="width:20px"/>'
    });
map.addControl(global_measuring_toolbox);

map.addControl(new L.control.coordinates({
    position:"bottomright",
    useDMS:false,
    decimals: 7,
	decimalSeperator: ",",
    labelTemplateLat:"N {y}",
    labelTemplateLng:"E {x}",
    useLatLngOrder:true,
    centerUserCoordinates: true,
    markerType: null
}).addTo(map));

function searchByAjax(text, callResponse){
	let items1=[];
	let items2=[];

	let ajaxCall=[
    $.ajax({//GeoNames
            url: 'https://ags.cuzk.cz/arcgis/rest/services/GEONAMES/Vyhledavaci_sluzba_nad_daty_GEONAMES/MapServer/exts/GeocodeSOE/suggest?maxSuggestions=100&outSR={"latestWkid":5514,"wkid":102067}&f=json',
            type: 'GET',
            data: { text: text },
            dataType: 'json',
            success: function (json) { items1 = json.suggestions;/*addLogText("Vyhledany GeoNames");*/ }
        }),
	$.ajax({//okres
		url:
		'https://ags.cuzk.cz/arcgis/rest/services/RUIAN/Vyhledavaci_sluzba_nad_daty_RUIAN/MapServer/exts/GeocodeSOE/tables/15/suggest?maxSuggestions=10&outSR={"latestWkid":5514,"wkid":102067}&f=json',
		type: 'GET',
		data: {text: text},
		dataType: 'json',
    success: function(json) {items2=json.suggestions;/*console.log("Vyhledany Okresy");*/}
		}),

	];
	Promise.all(ajaxCall).then(() => {/*console.log("Vyhledani ukonceno");*/callResponse( [...items2, ...items1]);})
}
