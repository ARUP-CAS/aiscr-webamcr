var global_map_can_edit = true;
var global_map_can_load_projects = true;
var boundsLock = 0;
var ORIGIN_KATASTR = "";

var poi_other = L.markerClusterGroup({ disableClusteringAtZoom: 20 })
var poi_sugest = L.layerGroup();
var poi_correct = L.layerGroup();

map.addLayer(poi_sugest);
map.addLayer(poi_correct);
map.addLayer(poi_other);

var heatPoints = [];
var heatmapOptions = settings_heatmap_options;
var heatLayer = L.heatLayer(heatPoints, heatmapOptions);

var global_clusters = false;
var global_heat = false;

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
        //Vratit puvodni katastr
        const select = $("input[name='hlavni_katastr']");
        if (global_map_can_edit && select && ORIGIN_KATASTR.length > 1) {
            select.val(ORIGIN_KATASTR);

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

var addPointOnLoad = (lat, long, text) => {
    if (text) {
        L.marker(amcr_static_coordinate_precision_wgs84([lat, long]), { icon: pinIconYellowDf, zIndexOffset: 2000 }).bindPopup(text).addTo(poi_sugest);
    } else {
        L.marker(amcr_static_coordinate_precision_wgs84([lat, long]), { icon: pinIconYellowDf, zIndexOffset: 2000 }).addTo(poi_sugest);
    }

    map.setView([lat, long], 18)
}

map.on('moveend', function () {
    switchMap(false);
});

heatPoints = heatPoints.map(function (p) {
    var bounds = map.getBounds();
    var northWest = bounds.getNorthWest(),
        southEast = bounds.getSouthEast();
    if (northWest.lat >= p[0] && southEast.lat <= p[0]) {
        if (northWest.lng <= p[1] && southEast.lng >= p[1]) {
            return [p[0], p[1]];
        }
    }
});

map.on('overlayadd overlayremove', function (e) {
    if (control._handlingClick) {
        if (e.name == "Projekty") {
            global_map_can_load_projects = !global_map_can_load_projects;
        }
    }
});

map.on('click', function (e) {
    const addPointToPoiLayer = (lat, long, text) => {
        if (global_map_can_edit) {
            poi_correct.clearLayers();
            L.marker([lat, long], { icon: pinIconRedDf }).bindPopup(text).addTo(poi_correct);
            const getUrl = window.location;
            const select = $("input[name='hlavni_katastr']");
            if (select) {
                fetch(getUrl.protocol + "//" + getUrl.host + `/heslar/zjisti-katastr-souradnic/?long=${long}&lat=${lat}`)
                    .then(response => response.json())
                    .then(response => {
                        if (ORIGIN_KATASTR.length == 0) {
                            ORIGIN_KATASTR = select.val();
                        }
                        select.val(response['value']);
                    })
            }
        }
    }

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

switchMap = function (overview = false) {
    var bounds = map.getBounds();
    let zoom = map.getZoom();
    var northWest = bounds.getNorthWest(),
        southEast = bounds.getSouthEast();
    if (global_map_can_load_projects) {
        if (overview || bounds.northWest != boundsLock.northWest || !boundsLock.northWest) {
            console.log("Change: " + northWest + "  " + southEast + " " + zoom);
            boundsLock = bounds;
            let xhr = new XMLHttpRequest();
            xhr.open('POST', '/projekt/akce-get-projekty');
            xhr.setRequestHeader('Content-type', 'application/json');
            if (typeof global_csrftoken !== 'undefined') {
                xhr.setRequestHeader('X-CSRFToken', global_csrftoken);
            }
            map.spin(false);
            map.spin(true);
            xhr.send(JSON.stringify(
                {
                    'northWest': northWest,
                    'southEast': southEast,
                    'zoom': zoom,
                }));
            xhr.onload = function () {
                poi_other.clearLayers();
                heatPoints = []
                map.removeLayer(heatLayer);
                let resAl = JSON.parse(this.responseText).algorithm
                if (resAl == "detail") {
                    let resPoints = JSON.parse(this.responseText).points
                    resPoints.forEach((i) => {
                        let ge = i.geom.split("(")[1].split(")")[0];

                        L.marker(amcr_static_coordinate_precision_wgs84([ge.split(" ")[1], ge.split(" ")[0]]), { icon: pinIconPurpleDf, zIndexOffset: 1000 }).bindPopup(i.ident_cely).addTo(poi_other)
                    })
                } else {
                    let resHeat = JSON.parse(this.responseText).heat
                    resHeat.forEach((i) => {
                        geom = i.geom.split("(")[1].split(")")[0].split(" ");
                        for (let j = 0; j < i.pocet; j++) {
                            heatPoints.push([geom[1], geom[0]])//chyba je to geome
                        }
                    })
                    heatLayer = L.heatLayer(heatPoints, heatmapOptions);
                    map.addLayer(heatLayer);
                    poi_other.clearLayers();
                }
                map.spin(false);
                //console.log("loaded")
            }
        }
    }
}
