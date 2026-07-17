
var poi = L.layerGroup();

var map = L.map('projectMap',{crs: JTSKcrs, attributionControl:false,zoomControl:false,  layers: [cuzkZM,poi]}).setView(init_position, 1);

var baseLayers = {
    [map_translations['cuzkzakladniMapyCr']]: cuzkZM,
    [map_translations['cuzkzakladniMapyCrGrey']]: cuzkZMGrey,
    [map_translations['cuzkOrtofotomapa']]: cuzkOrt,
    [map_translations['cuzkStinovanyeelief5G']]: cuzkEL,
};

var overlays = {
    [map_translations['cuzkKatastralniMapa']]: cuzkWMS,
    [map_translations['cuzkKatastralniUzemi']]: cuzkWMS2,
    [map_translations['npuPamatkovaOchrana']]: npuOchrana,
    [map_translations['lokalizace']]: poi
};

var global_map_layers = L.control.layers(baseLayers,overlays).addTo(map);
L.control.scale({imperial: false, metric: true,  maxWidth: 100}).addTo(map);

var searchControl=new L.Control.Search({
    position:'topleft',
    initial: false,
    marker: false,
    propertyName: 'text',
    propertyMagicKey:'magicKey',
    minLength:2,
    translations:leaflet_search_translations,
    layerKN:cuzkWMS
}).addTo(map);

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

let global_measuring_toolbox=new L.control.measure(
    {
        title: [map_translations['MeasureTitle']],
        icon:'<img src="'+static_url+'img/ruler-bold-32.png" style="width:20px"/>'
    });
map.addControl(global_measuring_toolbox);

map.addControl(new L.control.coordinates(
    {
    position:"bottomright",
    useDMS:false,
    decimals: 7,
	decimalSeperator: ",",
    labelTemplateLat:"N {y}",
    labelTemplateLng:"E {x}",
    useLatLngOrder:false,
    centerUserCoordinates: true,
    markerType: null
    }).addTo(map));

//Get Current Location
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition);
    } else {
        x.innerHTML = [map_translations['CurrentLocationError']]; // "Geolocation is not supported by this browser."
    }
}

//zobrazení DJ které daný pian obsahují
// addLogText je definován jen v mapa_arch_z.js; na ostatních mapách (PAS, mapový filtr) chybí,
// takže se na něj odkazujeme jen když existuje – jinak by klik na PIAN skončil ReferenceError
// a popup by zůstal prázdný.
function onMarkerClickLog(text) {
    if (typeof addLogText === "function") {
        addLogText(text);
    }
}

function onMarkerClick(ident_cely,e) {
    onMarkerClickLog("arch_z_detail_map.onMarkerClick")
    const popup = e.target.getPopup();
    popup.setContent("");
    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/pian/mapa-connections/'+ident_cely);
    xhr.setRequestHeader('Content-type', 'application/json');
    if (typeof global_csrftoken !== 'undefined') {
        xhr.setRequestHeader('X-CSRFToken', global_csrftoken);
    }
    xhr.send();
    xhr.onload = function () {
        rs = JSON.parse(this.responseText).points
        text=""
        rs.forEach((i) => {
            try{
                let link='<a href="/id/' + i.dj + '" target="_blank">' + i.dj + '</a></br>'
                text = text + link
            } catch(e){
                onMarkerClickLog("err:"+e)
            }
        })
        if(text=="") text="--"
        popup.setContent(text);
    }
}

function setCursor() {
    if (map.getZoom() > 11 && (typeof global_map_can_edit === "undefined" || global_map_can_edit)) {
        map.getContainer().style.cursor = 'default';
    } else {
        map.getContainer().style.cursor = 'grab';
    }    
}

map.on('zoomend', function () {
    setCursor()
});

map.getContainer().style.cursor = 'grab';
