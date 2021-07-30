//var map = L.map('projectMap').setView([49.84, 15.17], 7);
//var poi = L.layerGroup();

var osmColor = L.tileLayer('http://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'OSM map', maxZoom: 19.99, minZoom: 6 }),
cuzkOrt = L.tileLayer('http://ags.cuzk.cz/arcgis/rest/services/ortofoto_wm/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'ortofoto_wm', maxZoom: 19.99, minZoom: 6 }),
cuzkEL = L.tileLayer.wms('http://ags.cuzk.cz/arcgis2/services/dmr5g/ImageServer/WMSServer?', { layers: 'dmr5g:GrayscaleHillshade', maxZoom: 20, minZoom: 6 }),
cuzkZM = L.tileLayer('http://ags.cuzk.cz/arcgis/rest/services/zmwm/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'zmwm', maxZoom: 19.99, minZoom: 6 });

var map = L.map('projectMap',{zoomControl:false,  layers: [cuzkZM], fullscreenControl: true}).setView([49.84, 15.17], 7);

var baseLayers = {
        "Mapa ČR": osmColor,
        "Základní mapa": cuzkZM,
        "Ortofotomapa": cuzkOrt,
        "Stínovaný reliéf 5G": cuzkEL,
    };

var poi_other = L.layerGroup();

var overlays ={
    "Katastrální mapa":  L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'KN', maxZoom: 20.99, minZoom: 17, opacity: 0.5 }),
    "Katastrální území": L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'prehledka_kat_uz', maxZoom: 20.99, minZoom: 12, opacity: 0.5 }),
    "Projekty": poi_other

}

L.control.layers(baseLayers,overlays).addTo(map);
L.control.scale(metric = "true").addTo(map);
L.control.zoom(
    {
        zoomInText:'+',
        zoomInTitle:'Zvětšit',
        zoomOutText:'-',
        zoomOutTitle:'Zmenšit'
    }).addTo(map)

var poi = L.layerGroup();
map.addLayer(poi);

var addPointToPoiLayer = (lat, long, text) => {
        L.marker([lat, long]).bindPopup(text).addTo(poi);
}

map.on('click', function (e) {
    poi.clearLayers();
	let corX = e.latlng.lat;
    let corY = e.latlng.lng;
    if(corY>=12.2401111182 && corY<=18.8531441586 && corX>=48.5553052842 && corX<=51.1172677679)
	if (map.getZoom() > 15) {
		document.getElementById('id_latitude').value = corX
		document.getElementById('id_longitude').value = corY
        //$("#detector_coordinates_x").change();
        //$("#detector_coordinates_y").change();
        addPointToPoiLayer(corX, corY, 'Vámi vybraná poloha záměru');
        let xhr = new XMLHttpRequest();
        xhr.open('POST', '/oznameni/get-katastr-from-point');
        xhr.setRequestHeader('Content-type', 'application/json');
        if (typeof global_csrftoken !== 'undefined') {
            xhr.setRequestHeader('X-CSRFToken', global_csrftoken );
        }
        xhr.onload = function () {
            // do something to response
            console.log(JSON.parse(this.responseText).cadastre);
            let uzemi = document.getElementById('id_katastralni_uzemi');
            uzemi.value=JSON.parse(this.responseText).cadastre;
        };
        xhr.send(JSON.stringify({ 'corY': corY,'corX': corX }))

    } else {
        var zoom=2;
        if(map.getZoom()<10) zoom+=2;
        else if(map.getZoom()<13) zoom+=1;

        map.setView(e.latlng, map.getZoom() + zoom);
        //console.log("Your zoom is: "+map.getZoom())
    }
});
