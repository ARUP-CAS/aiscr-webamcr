var global_map_can_edit = true;

var poi_other = L.markerClusterGroup({disableClusteringAtZoom:20})

var osmColor = L.tileLayer('http://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'OSM map', maxZoom:25, maxNativeZoom: 19, minZoom: 6 }),
        cuzkWMS = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'KN', maxZoom:25, maxNativeZoom: 20, minZoom: 17, opacity: 0.5 }),
        cuzkWMS2 = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'prehledka_kat_uz', maxZoom:25, maxNativeZoom: 20, minZoom: 12, opacity: 0.5 }),
        cuzkOrt = L.tileLayer('http://ags.cuzk.cz/arcgis/rest/services/ortofoto_wm/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'ortofoto_wm', maxZoom:25, maxNativeZoom: 19, minZoom: 6 }),
        cuzkEL = L.tileLayer.wms('http://ags.cuzk.cz/arcgis2/services/dmr5g/ImageServer/WMSServer?', { layers: 'dmr5g:GrayscaleHillshade', maxZoom: 25, maxNativeZoom: 20, minZoom: 6 }),
        cuzkZM = L.tileLayer('http://ags.cuzk.cz/arcgis/rest/services/zmwm/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'zmwm', maxZoom: 25,maxNativeZoom:19, minZoom: 6 });

    var map = L.map('projectMap', {
        zoomControl:false,
        center: [49.84, 15.17],
        zoom: 7,
        layers: [cuzkZM, poi_other],
        fullscreenControl: true,
    }).setView([49.84, 15.17], 7);;

    var baseLayers = {
        "ČÚZK - Základní mapy ČR": cuzkZM,
        "ČÚZK - Ortofotomapa": cuzkOrt,
        "ČÚZK - Stínovaný reliéf 5G": cuzkEL,
        "OpenStreetMap": osmColor,
    };

    var overlays = {
        "ČÚZK - Katastrální mapa": cuzkWMS,
        "ČÚZK - Katastrální území": cuzkWMS2,
        "Projekty": poi_other
    };

    L.control.layers(baseLayers, overlays).addTo(map);
    L.control.scale(metric = "true").addTo(map);


    L.control.zoom(
        {
            zoomInText: '+',
            zoomInTitle: 'Zvětšit',
            zoomOutText: '-',
            zoomOutTitle: 'Zmenšit'
        }).addTo(map);

    L.control.measure().addTo(map)

L.control.coordinates({
    position:"bottomright",
    useDMS:true,
    labelTemplateLat:"N {y}",
    labelTemplateLng:"E {x}",
    useLatLngOrder:true,
    centerUserCoordinates: true,
    markerType: null
}).addTo(map);

//var map = L.map('projectMap').setView([49.84, 15.17], 7);
var poi_sugest = L.layerGroup();
var poi_correct = L.layerGroup();

L.easyButton('bi bi-skip-backward-fill', function () {
    poi_correct.clearLayers();
    if (poi_sugest.getLayers().length) {
        let ll = poi_sugest.getLayers()[0]._latlng;
        map.setView(ll, 18);
        try {
            document.getElementById('id_latitude').value = ll.lat;
            document.getElementById('id_longitude').value = ll.lng;
        } catch (e) {
            console.log("Error: Element id_latitude/latitude doesn exists")
        }
    }
}).addTo(map)


var button_map_lock = L.easyButton({
    states: [{
        stateName: 'add-lock',
        icon: 'bi bi-lock',
        title: 'add-lock',
        onClick: function (control) {
            global_map_can_edit = !global_map_can_edit;
            control.state('remove-lock');
        }
    }, {
        icon: 'bi bi-geo-alt',
        stateName: 'remove-lock',
        onClick: function (control) {
            global_map_can_edit = !global_map_can_edit;
            control.state('add-lock');
        },
        title: 'remove markers'
    }]
});
button_map_lock.addTo(map)



//https://github.com/pointhi/leaflet-color-markers
var greenIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
})

var redIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
})

/*L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
    maxZoom: 18,
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, ' +
        'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
    id: 'mapbox/streets-v11',
    tileSize: 512,
    zoomOffset: -1
}).addTo(map);*/
map.addLayer(poi_sugest);
map.addLayer(poi_correct);
map.addLayer(poi_other);

//adding other points to layer
var getOtherPoi = () => {

    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/projekt/get-points-arround-point');
    xhr.setRequestHeader('Content-type', 'application/json');
    if (typeof global_csrftoken !== 'undefined') {
        xhr.setRequestHeader('X-CSRFToken', global_csrftoken);
    }
    xhr.onload = function () {
        // do something to response
        poi_other.clearLayers();
        //console.log(poi_sugest.getLayers()[0]._latlng)
        JSON.parse(this.responseText).points.forEach((point) => {
            //if(poi_sugest.getLayers().length>0 && poi_sugest.getLayers()[0]._latlng.lat!=point.lat && poi_sugest.getLayers()[0]._latlng.lng !=point.lng)
            L.marker([point.lat, point.lng]).bindPopup(point.ident_cely).addTo(poi_other)
        })
    };
    xhr.send(JSON.stringify({ 'NorthWest': map.getBounds().getNorthWest(), 'SouthEast': map.getBounds().getSouthEast() }))
}

const addPointToPoiLayer = (lat, long, text) => {
    if (global_map_can_edit) {
        poi_correct.clearLayers();
        L.marker([lat, long], { icon: redIcon }).bindPopup(text).addTo(poi_correct);
        const getUrl = window.location;
        const select = $("#id_hlavni_katastr");
        if (select) {
            fetch(getUrl.protocol + "//" + getUrl.host + `/heslar/zjisti-katastr-souradnic/?long=${long}&lat=${lat}`)
                .then(response => response.json())
                .then(response => {
                    select.val(response['value']);
                })
        }
        //console.log(lat+'  '+ long)
    }
}

var addPointOnLoad = (lat, long, text) => {
    if (text) {
        L.marker([lat, long], { icon: greenIcon }).bindPopup(text).addTo(poi_sugest);
    } else {
        L.marker([lat, long], { icon: greenIcon }).addTo(poi_sugest);
    }

    map.setView([lat, long], 18)
    //getOtherPoi();
}

map.on('zoomend', function () {
    if (map.getZoom() > 10) {
        getOtherPoi();
    }
});

map.on('click', function (e) {
    console.log("Your zoom is: " + map.getZoom())

    let corX = e.latlng.lat;
    let corY = e.latlng.lng;
    if (corY >= 12.2401111182 && corY <= 18.8531441586 && corX >= 48.5553052842 && corX <= 51.1172677679)
        if (map.getZoom() > 15) {
            try {
                document.getElementById('id_latitude').value = corX
                document.getElementById('id_longitude').value = corY
            } catch (e) {
                console.log("Error: Element id_latitude/latitude doesn exists")
            }
            //$("#detector_coordinates_x").change();
            //$("#detector_coordinates_y").change();
            addPointToPoiLayer(corX, corY, 'Vámi vybraná poloha záměru');
            //getOtherPoi();
            /*let xhr = new XMLHttpRequest();
            xhr.open('POST', '/oznameni/get-katastr-from-point');
            xhr.setRequestHeader('Content-type', 'application/json');
            if (typeof global_csrftoken !== 'undefined') {
                xhr.setRequestHeader('X-CSRFToken', global_csrftoken );
            }
            xhr.onload = function () {
                // do something to response
                console.log(JSON.parse(this.responseText).cadastre);
                document.getElementById('katastr_name').innerHTML=JSON.parse(this.responseText).cadastre;
            };
            xhr.send(JSON.stringify({ 'corY': corY,'corX': corX }))*/

        } else {
            var zoom = 2;
            if (map.getZoom() < 10) zoom += 2;
            else if (map.getZoom() < 13) zoom += 1;

            map.setView(e.latlng, map.getZoom() + zoom);
            //console.log("Your zoom is: "+map.getZoom())
        }
});
