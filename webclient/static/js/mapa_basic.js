var osmColor = L.tileLayer('http://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'OSM map', maxZoom:25, maxNativeZoom: 19, minZoom: 6 }),
    cuzkWMS = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'KN', maxZoom:25, maxNativeZoom: 20, minZoom: 17, opacity: 0.5 }),
    cuzkWMS2 = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'prehledka_kat_uz', maxZoom:25, maxNativeZoom: 20, minZoom: 12, opacity: 0.5 }),
    cuzkOrt = L.tileLayer('http://ags.cuzk.cz/arcgis/rest/services/ortofoto_wm/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'ortofoto_wm', maxZoom:25, maxNativeZoom: 19, minZoom: 6 }),
    cuzkEL = L.tileLayer.wms('http://ags.cuzk.cz/arcgis2/services/dmr5g/ImageServer/WMSServer?', { layers: 'dmr5g:GrayscaleHillshade', maxZoom: 25, maxNativeZoom: 20, minZoom: 6 }),
    cuzkZM = L.tileLayer('http://ags.cuzk.cz/arcgis/rest/services/zmwm/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'zmwm', maxZoom: 25,maxNativeZoom:19, minZoom: 6 });


var poi = L.layerGroup();
var map = L.map('projectMap',{attributionControl:false,zoomControl:false,  layers: [cuzkZM]}).setView([49.84, 15.17], 7);

var baseLayers = {
    "ČÚZK - Základní mapy ČR": cuzkZM,
    "ČÚZK - Ortofotomapa": cuzkOrt,
    "ČÚZK - Stínovaný reliéf 5G": cuzkEL,
    "OpenStreetMap": osmColor,
};

var overlays = {
    "ČÚZK - Katastrální mapa": cuzkWMS,
    "ČÚZK - Katastrální území": cuzkWMS2,
};

global_map_layers = L.control.layers(baseLayers,overlays).addTo(map);
L.control.scale(metric = "true").addTo(map);
map.addControl(new L.Control.Fullscreen({
    title: {
        'false': 'Celá obrazovka',
        'true': 'Opustit celou obrazovku'
    }
}));
map.addControl(new L.control.zoom(
    {
        zoomInText:'+',
        zoomInTitle:'Přiblížit',
        zoomOutText:'-',
        zoomOutTitle:'Oddálit'
    }))

var searchControl=new L.Control.Search({
    position:'topleft',
    sourceData: searchByAjax,
    initial: false,
    zoom: 12,
    marker: false,
    textPlaceholder:'Vyhledej',
    textCancel: 'Zruš',
    propertyName: 'text',
    propertyMagicKey:'magicKey',
    propertyMagicKeyUrl:'https://ags.cuzk.cz/arcgis/rest/services/RUIAN/Vyhledavaci_sluzba_nad_daty_RUIAN/MapServer/exts/GeocodeSOE/tables/{*}/findAddressCandidates?outSR={"wkid":4258}&f=json',
    textErr: 'Nenalezeno',
    minLength:3
}).addTo(map);

let global_measuring_toolbox=new L.control.measure(
    {
        title:"Měřit vzdálenost",
        icon:'<img src="'+static_url+'/img/ruler-bold-32.png" style="width:20px"/>'
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
	 $.ajax({//obec
		url:
		'https://ags.cuzk.cz/arcgis/rest/services/RUIAN/Vyhledavaci_sluzba_nad_daty_RUIAN/MapServer/exts/GeocodeSOE/tables/12/suggest?maxSuggestions=10&outSR={"latestWkid":5514,"wkid":102067}&f=json',
		type: 'GET',
		data: {text: text},
		dataType: 'json',
		success: function(json) {items1=json.suggestions;/*console.log("Vyhledany Obce");*/}
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
