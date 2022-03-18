var global_map_can_edit = true;

var poi_other = L.markerClusterGroup({ disableClusteringAtZoom: 20 })
var poi_sugest = L.layerGroup();
var poi_correct = L.layerGroup();

map.addLayer(poi_sugest);
map.addLayer(poi_correct);
map.addLayer(poi_other);

var overlays = {
    "ČÚZK - Katastrální mapa": cuzkWMS,
    "ČÚZK - Katastrální území": cuzkWMS2,
    "Projekty": poi_other
};

global_map_layers.remove(map);//remove previous overlay
L.control.layers(baseLayers, overlays).addTo(map);

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
}, 'Výchozí stav ').addTo(map)


var button_map_lock = L.easyButton({
    states: [{
        stateName: 'add-lock',
        icon: 'bi bi-lock',
        title: 'Vypnout‌ ‌editaci‌‌',
        onClick: function (control) {
            global_map_can_edit = !global_map_can_edit;
            control.state('remove-lock');
        }
    }, {
        icon: 'bi bi-geo-alt',
        stateName: 'remove-lock',
        title: 'Zapnout‌ ‌editaci‌',
        onClick: function (control) {
            global_map_can_edit = !global_map_can_edit;
            control.state('add-lock');
        }
    }]
}).addTo(map);

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

//adding other points to layer
var getOtherPoi = () => {

    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/projekt/projekt-zjisti-okolni-projekty');
    xhr.setRequestHeader('Content-type', 'application/json');
    if (typeof global_csrftoken !== 'undefined') {
        xhr.setRequestHeader('X-CSRFToken', global_csrftoken);
    }
    xhr.onload = function () {
        poi_other.clearLayers();
        JSON.parse(this.responseText).points.forEach((point) => {
            L.marker(amcr_static_coordinate_precision_wgs84([point.lat, point.lng])).bindPopup(point.ident_cely).addTo(poi_other)
        })
    };
    xhr.send(JSON.stringify({ 'NorthWest': map.getBounds().getNorthWest(), 'SouthEast': map.getBounds().getSouthEast() }))
}



var addPointOnLoad = (lat, long, text) => {
    if (text) {
        L.marker(amcr_static_coordinate_precision_wgs84([lat, long]), { icon: greenIcon }).bindPopup(text).addTo(poi_sugest);
    } else {
        L.marker(amcr_static_coordinate_precision_wgs84([lat, long]), { icon: greenIcon }).addTo(poi_sugest);
    }

    map.setView([lat, long], 18)
}

map.on('zoomend', function () {
    if (map.getZoom() > 10) {
        getOtherPoi();
    }
});

map.on('moveend', function () {
    if (map.getZoom() > 10) {
        getOtherPoi();
    }
});

map.on('click', function (e) {
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
        }
    }
    //console.log("Your zoom is: " + map.getZoom())
    //console.log("Clicked Position is: "+e.latlng.lat+" "+e.latlng.lng)

    let [corX, corY] = amcr_static_coordinate_precision_wgs84([e.latlng.lat, e.latlng.lng]);
    if (!global_measuring_toolbox._measuring)
        if (corY >= 12.2401111182 && corY <= 18.8531441586 && corX >= 48.5553052842 && corX <= 51.1172677679)
            if (map.getZoom() > 15) {
                try {
                    //console.log("Position is: "+corX+" "+corY)
                    document.getElementById('id_latitude').value = corX
                    document.getElementById('id_longitude').value = corY
                } catch (e) {
                    console.log("Error: Element id_latitude/latitude doesn exists")
                }
                addPointToPoiLayer(corX, corY, 'Vámi vybraná poloha záměru');

            } else {
                var zoom = 2;
                if (map.getZoom() < 10) zoom += 2;
                else if (map.getZoom() < 13) zoom += 1;

                map.setView(e.latlng, map.getZoom() + zoom);
            }
});
