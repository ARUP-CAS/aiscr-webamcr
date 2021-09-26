//var map = L.map('projectMap').setView([49.84, 15.17], 7);
//var poi = L.layerGroup();
var osmColor = L.tileLayer('http://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'OSM map', maxZoom:25, maxNativeZoom: 19, minZoom: 6 }),
    cuzkWMS = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'KN', maxZoom:25, maxNativeZoom: 20, minZoom: 17, opacity: 0.5 }),
    cuzkWMS2 = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'prehledka_kat_uz', maxZoom:25, maxNativeZoom: 20, minZoom: 12, opacity: 0.5 }),
    cuzkOrt = L.tileLayer('http://ags.cuzk.cz/arcgis/rest/services/ortofoto_wm/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'ortofoto_wm', maxZoom:25, maxNativeZoom: 19, minZoom: 6 }),
    cuzkEL = L.tileLayer.wms('http://ags.cuzk.cz/arcgis2/services/dmr5g/ImageServer/WMSServer?', { layers: 'dmr5g:GrayscaleHillshade', maxZoom: 25, maxNativeZoom: 20, minZoom: 6 }),
    cuzkZM = L.tileLayer('http://ags.cuzk.cz/arcgis/rest/services/zmwm/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'zmwm', maxZoom: 25,maxNativeZoom:19, minZoom: 6 });

var poi_other = L.layerGroup();

var map = L.map('projectMap',{zoomControl:false,  layers: [cuzkZM], fullscreenControl: true}).setView([49.84, 15.17], 7);

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
            if(JSON.parse(this.responseText).cadastre=="None"){
                //console.log("run")
                alert("Neplatny bod, klikli jste mimo území ČR")
                console.log("Neplatny bod, klikli jste mimo území ČR")
                //var mess='<li><div class="alert alert-info msg fade show" role="alert">Klikli jste mimo území ČR</div></li>'
                //document.getElementById('messages-list').append(mess)
                //$("#messages").append(message);
                //mess.fadeIn(500);
            } else {
                const uzemi = document.getElementById('id_katastralni_uzemi');
                uzemi.value=JSON.parse(this.responseText).cadastre;
            }
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
